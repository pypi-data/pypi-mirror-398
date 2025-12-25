import os
import pathlib

from fbnconfig import Deployment, drive, lumi
from fbnconfig import workflows as wf


def configure(host_vars) -> Deployment:
    deployment_name = getattr(host_vars, "name", "fbnconfig_quality_control_wf")
    file_name = "exampledata.xlsx"

    base_folder = drive.FolderResource(
        id="base_folder", name=f"fbnconfig-{deployment_name}", parent=drive.root
    )
    excel_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "data", file_name)
    deployment_folder = drive.FolderResource(id="sub_folder", name=deployment_name, parent=base_folder)

    spreadsheet = drive.FileResource(
        id="xslx", folder=deployment_folder, name=file_name, content_path=pathlib.PurePath(excel_path)
    )

    import_from_excel_view = lumi.ViewResource(
        id="import-from-excel-view",
        provider=f"Views.fbnconfig.import_excel_{deployment_name}",
        description="I am a view",
        sql="""
            @@filename = select #PARAMETERVALUE(filename);
            @@quote_scope = select #PARAMETERVALUE(quote_scope);

            -- Load data from Excel
            @inst_data = use Drive.Excel with @@filename
                --file={@@filename}
                --worksheet=instrument
            enduse;

            @quote_data = use Drive.Excel with @@filename
                --file={@@filename}
                --worksheet=price_time_series
            enduse;

            -- Transform quote data
            @quotes_for_upload =
                select
                    'ClientInternal' as InstrumentIdType,
                    instrument_id as InstrumentId,
                    @@quote_scope as QuoteScope,
                    'Price' as QuoteType,
                    'Lusid' as Provider,
                    'Mid' as Field,
                    price_date as QuoteEffectiveAt,
                    price as Value,
                    ccy as Unit
                from @quote_data;

            -- Transform instrument data
            @equity_instruments =
                select
                    inst_id as ClientInternal,
                    name as DisplayName,
                    ccy as DomCcy,
                    @@quote_scope as Scope
                from @inst_data;


            -- Return quotes in view
            select * from @quotes_for_upload;

            -- Create instruments if not Active
            select *
            from Lusid.Instrument.Equity.Writer
            where ToWrite = @equity_instruments;

            -- Upload quotes into LUSID
            select *
            from Lusid.Instrument.Quote.Writer
            where ToWrite = @quotes_for_upload
        """,
        parameters=[
            lumi.Parameter(
                name="filename",
                value=f"{spreadsheet.path()}",
                set_as_default_value=False,
                tooltip="Drive filepath",
                type=lumi.ParameterType.Text,
            ),
            lumi.Parameter(
                name="quote_scope",
                value=deployment_name,
                set_as_default_value=False,
                tooltip="Scope to load quotes in",
                type=lumi.ParameterType.Text,
            ),
        ],
        dependencies=[spreadsheet],
    )

    reasonable_value_check_view = lumi.ViewResource(
        id="reasonable-value-check",
        provider=f"Views.fbnconfig.reasonable_value_{deployment_name}",
        sql="""
            @@quote_scope = select #PARAMETERVALUE(quote_scope);
            -- Collect quotes for all instruments
            @quotes_data = select *
                from Lusid.Instrument.Quote
                where QuoteScope = @@quote_scope
                    and InstrumentIdType = 'ClientInternal'
                    and QuoteType = 'Price';

            -- Collect instrument static
            @instrument_data = select
                ClientInternal,
                DisplayName
                from Lusid.Instrument.Equity
                where @@quote_scope = Scope
                    and State = 'Active';

            -- Generate time series
            @price_ts = select
                ClientInternal,
                DisplayName,
                QuoteEffectiveAt as [PriceDate],
                Unit as [Currency],
                Value as [Price],
                Field
                from @instrument_data i
                join @quotes_data q on (i.ClientInternal = q.InstrumentId);

            -- Run reasonable value check for each quote
            @result = select
                PriceDate,
                @@quote_scope as QuoteScope,
                ClientInternal,
                DisplayName,
                Price,
                Field,
                case
                    when Price >= 1000 then 'Unreasonably Large Value'
                    when Price <= 1 then 'Unreasonably Small Value'
                    else 'OK'
                end as Result
                from @price_ts
                where not Result = 'OK';

            select #SELECT {
                {PriceDate~DateTime : PriceDate},
                {QuoteScope~Text : QuoteScope},
                {ClientInternal~Text : ClientInternal},
                {DisplayName~Text : DisplayName},
                {Price~Decimal : Price},
                {Field~Text : Field},
                {Result~Text : Result}
                }
                from @result;
        """,
        description="Ensure a quote's price is a sensible value (between 1 and 1000)",
        parameters=[
            lumi.Parameter(
                name="quote_scope",
                value=deployment_name,
                set_as_default_value=True,
                tooltip="Scope to check quotes in",
                type=lumi.ParameterType.Text,
            )
        ],
    )

    iqr_outlier_view = lumi.ViewResource(
        id="iqr_outlier",
        provider=f"Views.fbnconfig.iqr_outlier_{deployment_name}",
        sql="""
            @@quote_scope = select #PARAMETERVALUE(quote_scope);
            -- Collect quotes for all instruments
            @quotes_data = select *
                from Lusid.Instrument.Quote
                where QuoteScope = @@quote_scope
                    and InstrumentIdType = 'ClientInternal'
                    and QuoteType = 'Price';

            -- Collect instrument static
            @instrument_data = select
                ClientInternal,
                DisplayName
                from Lusid.Instrument.Equity
                where @@quote_scope = Scope
                    and State = 'Active';

            -- Generate time series
            @price_ts = select
                ClientInternal,
                DisplayName,
                Field,
                QuoteEffectiveAt as [PriceDate],
                Unit as [Currency],
                Value as [Price]
                from @instrument_data i
                join @quotes_data q on (i.ClientInternal = q.InstrumentId);
             -- Run IQR checks for each instrument
            @iqr_data = select
                ClientInternal,
                interquartile_range(price) * (1.5) as [iqr_x1_5],
                quantile(price, 0.25) as [q1],
                quantile(price, 0.75) as [q3]
                from @price_ts
                group by ClientInternal;

            -- Join the IQR data with the time series and identify outliers
            @result = select
                p.PriceDate as PriceDate,
                @@quote_scope as QuoteScope,
                p.ClientInternal,
                p.DisplayName as DisplayName,
                i.q1,
                i.q3,
                (i.q3 + i.iqr_x1_5) as [UpperLimit],
                (i.q1 - i.iqr_x1_5) as [LowerLimit],
                p.Price as Price,
                Field,
                case when p.Price not between (i.q1 - i.iqr_x1_5) and (i.q3 + i.iqr_x1_5)
                    then 'IQR Outlier'
                    else 'OK'
                end as Result
                from @price_ts p
                join @iqr_data i on p.ClientInternal = i.ClientInternal
                where not Result = 'OK';

                select #SELECT {
                    {PriceDate~DateTime : PriceDate},
                    {QuoteScope~Text : QuoteScope},
                    {ClientInternal~Text : ClientInternal},
                    {DisplayName~Text : DisplayName},
                    {Price~Decimal : Price},
                    {Field~Text : Field},
                    {Result~Text : Result}
                }
                from @result;
         """,
        description="Find any outlier quotes for a given instrument using the interquartile range. "
        "This uses the 1.5 * IQR rule, that is, "
        "to find any quotes that fall between Q1 - 1.5 * IQR or above Q3 + 1.5 * IQR",
        parameters=[
            lumi.Parameter(
                name="quote_scope",
                value=deployment_name,
                set_as_default_value=True,
                tooltip="Scope to check quotes in",
                type=lumi.ParameterType.Text,
            )
        ],
    )
    quotes_update_view = lumi.ViewResource(
        id="quotes_update_view",
        provider=f"Views.fbnconfig.quote_writer_{deployment_name}",
        sql="""
            @@quote_scope = select #PARAMETERVALUE(quote_scope);
            @@instrument_id = select #PARAMETERVALUE(instrument_id);
            @@field_type = select #PARAMETERVALUE(field_type);
            @@price = select #PARAMETERVALUE(price);
            @@effective_at = select #PARAMETERVALUE(effective_at);

            @table_of_data =
                select
                    @@quote_scope as QuoteScope,
                    'Lusid' as Provider,
                    @@instrument_id as InstrumentId,
                    'ClientInternal' as InstrumentIdType,
                    'Price' as QuoteType,
                    @@field_type as Field,
                    @@price as Value,
                    'GBP' as Unit,
                    @@effective_at as QuoteEffectiveAt;

            select * from Lusid.Instrument.Quote.Writer where ToWrite = @table_of_data;
         """,
        description="I am a view",
        parameters=[
            lumi.Parameter(
                name="quote_scope",
                value=deployment_name,
                set_as_default_value=True,
                tooltip="Scope to check quotes in",
                type=lumi.ParameterType.Text,
            ),
            lumi.Parameter(
                name="instrument_id",
                value="",
                set_as_default_value=False,
                tooltip="Instrument id to load given quote for",
                type=lumi.ParameterType.Text,
            ),
            lumi.Parameter(
                name="field_type",
                value="",
                set_as_default_value=False,
                tooltip="Quote field type. Mid.",
                type=lumi.ParameterType.Text,
            ),
            lumi.Parameter(
                name="price",
                value=0,
                set_as_default_value=False,
                tooltip="Quote price",
                type=lumi.ParameterType.Decimal,
            ),
            lumi.Parameter(
                name="effective_at",
                value="2024-01-18",
                set_as_default_value=False,
                tooltip="Date to load the quote for",
                type=lumi.ParameterType.DateTime,
            ),
        ],
        use_dry_run=True,
    )

    import_from_excel_worker = wf.WorkerResource(
        id="import_from_excel_worker-example",
        scope=deployment_name,
        code="ImportFromExcelFile",
        display_name="Import From Excel",
        description="Imports quote data from specified Excel file in Drive.",
        worker_configuration=wf.LuminesceView(view=import_from_excel_view),
    )

    reasonable_value_worker = wf.WorkerResource(
        id="reasonable_value_worker-example",
        scope=deployment_name,
        code="ReasonableValueChecker",
        display_name="Reasonable Value Checker",
        description="Find any quotes with values not between 1 and 1000.",
        worker_configuration=wf.LuminesceView(view=reasonable_value_check_view),
    )

    iqr_outliers_worker = wf.WorkerResource(
        id="iqr_outliers_worker-example",
        scope=deployment_name,
        code="IQROutliers",
        display_name="IQR Outliers",
        description="Find any IQR outlier quotes.",
        worker_configuration=wf.LuminesceView(view=iqr_outlier_view),
    )

    quotes_update_worker = wf.WorkerResource(
        id="quotes_update_worker-example",
        scope=deployment_name,
        code="QuoteUpdate",
        display_name="Quote update",
        description="Update quote based on provided parameters",
        worker_configuration=wf.LuminesceView(view=quotes_update_view),
    )

    def external_trigger(name: str) -> wf.TriggerDefinition:
        return wf.TriggerDefinition(name=name, type="External")

    # Common triggers
    start_trigger = external_trigger(name="Start")
    resolved_trigger = external_trigger(name="Resolved")
    place_on_hold_trigger = external_trigger(name="PlaceOnHold")
    resume_trigger = external_trigger(name="Resume")
    ignore_trigger = external_trigger(name="Ignore")
    updated_trigger = external_trigger(name="Updated")
    no_exceptions_trigger = external_trigger(name="NoExceptions")
    exceptions_found_trigger = external_trigger(name="ExceptionsFound")

    # Common actions
    resolve_parent_action = wf.ActionDefinition(
        name="resolved-trigger-parent",
        action_details=wf.TriggerParentTaskAction(trigger=resolved_trigger),
    )

    # Common fields
    quote_scope_field: wf.TaskFieldDefinition = wf.TaskFieldDefinition(
        name="QuoteScope", type=wf.TaskFieldDefinitionType.STRING
    )

    # Common states
    pending_state = wf.TaskStateDefinition(name="Pending")
    in_dq_control_state = wf.TaskStateDefinition(name="InDQControl")
    exceptions_state = wf.TaskStateDefinition(name="Exceptions")
    complete_state = wf.TaskStateDefinition(name="Complete")
    resolved_state = wf.TaskStateDefinition(name="Resolved")
    ignored_state = wf.TaskStateDefinition(name="Ignored")
    in_progress_state = wf.TaskStateDefinition(name="InProgress")
    on_hold_state = wf.TaskStateDefinition(name="OnHold")
    # Common child task exception fields

    common_child_task_fields: dict[str | wf.TaskFieldDefinition, wf.FieldMapping] = {
        quote_scope_field: wf.FieldMapping(map_from=quote_scope_field),  # pyright: ignore
        "PriceDate": wf.FieldMapping(map_from="PriceDate"),
        "ClientInternal": wf.FieldMapping(map_from="ClientInternal"),
        "DisplayName": wf.FieldMapping(map_from="DisplayName"),
        "Price": wf.FieldMapping(map_from="Price"),
        "Result": wf.FieldMapping(map_from="Result"),
        "Field": wf.FieldMapping(map_from="Field"),
    }
    update_quote_action = wf.ActionDefinition(
        name="update-quote",
        action_details=wf.RunWorkerAction(
            worker=quotes_update_worker,
            worker_parameters={
                "quote_scope": wf.FieldMapping(map_from=quote_scope_field),
                "instrument_id": wf.FieldMapping(map_from="ClientInternal"),
                "field_type": wf.FieldMapping(map_from="Field"),
                "price": wf.FieldMapping(map_from="Price"),
                "effective_at": wf.FieldMapping(map_from="PriceDate"),
            },
            worker_status_triggers=wf.WorkerStatusTriggers(
                completed_with_results=updated_trigger, completed_no_results=place_on_hold_trigger
            ),
        ),
    )

    handle_exception_task_definition = wf.TaskDefinitionResource(
        id="handle_exception_task_definition",
        scope=deployment_name,
        code="HandleException",
        display_name="Handle Exception",
        description="Handle any data outliers that are raised.",
        states=[
            pending_state,
            in_progress_state,
            resolved_state,
            on_hold_state,
            ignored_state,
            complete_state,
        ],
        field_schema=[
            quote_scope_field,
            wf.TaskFieldDefinition(name="PriceDate", type=wf.TaskFieldDefinitionType.DATETIME),
            wf.TaskFieldDefinition(name="ClientInternal", type=wf.TaskFieldDefinitionType.STRING),
            wf.TaskFieldDefinition(name="DisplayName", type=wf.TaskFieldDefinitionType.STRING),
            wf.TaskFieldDefinition(name="Price", type=wf.TaskFieldDefinitionType.DECIMAL),
            wf.TaskFieldDefinition(name="Field", type=wf.TaskFieldDefinitionType.STRING),
            wf.TaskFieldDefinition(name="Result", type=wf.TaskFieldDefinitionType.STRING),
            wf.TaskFieldDefinition(name="Details", type=wf.TaskFieldDefinitionType.STRING),
        ],
        initial_state=wf.InitialState(
            name=pending_state,
            required_fields=[
                quote_scope_field,
                "PriceDate",
                "ClientInternal",
                "DisplayName",
                "Price",
                "Result",
            ],
        ),
        triggers=[
            start_trigger,
            resolved_trigger,
            place_on_hold_trigger,
            resume_trigger,
            ignore_trigger,
            updated_trigger,
        ],
        transitions=[
            wf.TaskTransitionDefinition(
                from_state=pending_state, to_state=in_progress_state, trigger=start_trigger
            ),
            wf.TaskTransitionDefinition(
                from_state=in_progress_state,
                to_state=resolved_state,
                trigger=resolved_trigger,
                guard="fields['Details'] neq ''",
                action=update_quote_action,
            ),
            wf.TaskTransitionDefinition(
                from_state=in_progress_state, to_state=on_hold_state, trigger=place_on_hold_trigger
            ),
            wf.TaskTransitionDefinition(
                from_state=on_hold_state, to_state=in_progress_state, trigger=resume_trigger
            ),
            wf.TaskTransitionDefinition(
                from_state=in_progress_state,
                to_state=ignored_state,
                trigger=ignore_trigger,
                guard="fields['Details'] neq ''",
                action=resolve_parent_action,
            ),
            wf.TaskTransitionDefinition(
                from_state=resolved_state,
                to_state=complete_state,
                trigger=updated_trigger,
                action=resolve_parent_action,
            ),
            wf.TaskTransitionDefinition(
                from_state=resolved_state, to_state=on_hold_state, trigger=place_on_hold_trigger
            ),
        ],
        actions=[resolve_parent_action, update_quote_action],
    )

    start_reasonable_value_action = wf.ActionDefinition(
        name="start_reasonable_value_action",
        action_details=wf.RunWorkerAction(
            worker=reasonable_value_worker,
            worker_parameters={"quote_scope": wf.FieldMapping(map_from=quote_scope_field)},
            worker_status_triggers=wf.WorkerStatusTriggers(
                completed_with_results=exceptions_found_trigger,
                completed_no_results=no_exceptions_trigger,
            ),
            child_task_configurations=[
                wf.ResultantChildTaskConfiguration(
                    child_task_configuration=wf.ChildTaskConfiguration(
                        task_definition=handle_exception_task_definition,
                        initial_trigger=start_trigger,
                        child_task_fields=common_child_task_fields,
                    )
                )
            ],
        ),
    )

    reasonable_value_control_task = wf.TaskDefinitionResource(
        id="reasonable_value_control_task",
        scope=deployment_name,
        code="ReasonableValueDataControl",
        display_name="Reasonable Value Data Control",
        description="Conduct reasonable value data control on quote data. Raise any exceptions.",
        states=[pending_state, in_dq_control_state, exceptions_state, resolved_state, complete_state],
        field_schema=[quote_scope_field],
        initial_state=wf.InitialState(name=pending_state, required_fields=[quote_scope_field]),
        triggers=[start_trigger, no_exceptions_trigger, exceptions_found_trigger, resolved_trigger],
        actions=[start_reasonable_value_action, resolve_parent_action],
        transitions=[
            wf.TaskTransitionDefinition(
                from_state=pending_state,
                to_state=in_dq_control_state,
                trigger=start_trigger,
                action=start_reasonable_value_action,
            ),
            wf.TaskTransitionDefinition(
                from_state=in_dq_control_state,
                to_state=complete_state,
                trigger=no_exceptions_trigger,
                action=resolve_parent_action,
            ),
            wf.TaskTransitionDefinition(
                from_state=in_dq_control_state,
                to_state=exceptions_state,
                trigger=exceptions_found_trigger,
            ),
            wf.TaskTransitionDefinition(
                from_state=exceptions_state,
                to_state=resolved_state,
                guard=f"childTasks all (state eq '{complete_state.name}' "
                f"or state eq '{ignored_state.name}')",
                trigger=resolved_trigger,
                action=resolve_parent_action,
            ),
        ],
    )

    start_iqr_outlier_action = wf.ActionDefinition(
        name="start-iqr-outlier-action",
        action_details=wf.RunWorkerAction(
            worker=iqr_outliers_worker,
            worker_parameters={"quote_scope": wf.FieldMapping(map_from=quote_scope_field)},
            worker_status_triggers=wf.WorkerStatusTriggers(
                completed_with_results=exceptions_found_trigger,
                completed_no_results=no_exceptions_trigger,
            ),
            child_task_configurations=[
                wf.ResultantChildTaskConfiguration(
                    child_task_configuration=wf.ChildTaskConfiguration(
                        initial_trigger=start_trigger,
                        task_definition=handle_exception_task_definition,
                        child_task_fields=common_child_task_fields,
                    )
                )
            ],
        ),
    )

    iqr_outlier_control_task = wf.TaskDefinitionResource(
        id="iqr_outlier_control_task",
        scope=deployment_name,
        code="IQROutlierDataControl",
        display_name="IQR Outlier Data Control",
        description="Conduct IQR outlier data control on quote data. Raise any exceptions.",
        states=[pending_state, in_dq_control_state, exceptions_state, complete_state, resolved_state],
        field_schema=[quote_scope_field],
        initial_state=wf.InitialState(name=pending_state, required_fields=[quote_scope_field]),
        triggers=[start_trigger, no_exceptions_trigger, exceptions_found_trigger, resolved_trigger],
        actions=[start_iqr_outlier_action, resolve_parent_action],
        transitions=[
            wf.TaskTransitionDefinition(
                from_state=pending_state,
                to_state=in_dq_control_state,
                trigger=start_trigger,
                action=start_iqr_outlier_action,
            ),
            wf.TaskTransitionDefinition(
                from_state=in_dq_control_state,
                to_state=complete_state,
                trigger=no_exceptions_trigger,
                action=resolve_parent_action,
            ),
            wf.TaskTransitionDefinition(
                from_state=in_dq_control_state,
                to_state=exceptions_state,
                trigger=exceptions_found_trigger,
            ),
            wf.TaskTransitionDefinition(
                from_state=exceptions_state,
                to_state=resolved_state,
                guard=f"childTasks all (state eq '{complete_state.name}' "
                f"or state eq '{ignored_state.name}')",
                trigger=resolved_trigger,
                action=resolve_parent_action,
            ),
        ],
    )

    start_import_action = wf.ActionDefinition(
        name="start-import-worker",
        action_details=wf.RunWorkerAction(
            worker=import_from_excel_worker,
            worker_parameters={
                "quote_scope": wf.FieldMapping(map_from=quote_scope_field),
                "filename": wf.FieldMapping(map_from="filename"),
            },
            worker_status_triggers=wf.WorkerStatusTriggers(
                completed_with_results="Imported",
                completed_no_results="Failure",
                failed_to_complete="Failure",
                failed_to_start="Failure",
            ),
        ),
    )

    create_reasonable_value_task_action = wf.ActionDefinition(
        name="create-reasonable-value-task",
        action_details=wf.CreateChildTasksAction(
            child_task_configurations=[
                wf.ChildTaskConfiguration(
                    task_definition=reasonable_value_control_task,
                    initial_trigger=start_trigger,
                    child_task_fields={
                        quote_scope_field: wf.FieldMapping(map_from=quote_scope_field)  # pyright: ignore
                    },
                )
            ]
        ),
    )

    create_iqr_outlier_task_action = wf.ActionDefinition(
        name="create-IQR-outlier-task",
        action_details=wf.CreateChildTasksAction(
            child_task_configurations=[
                wf.ChildTaskConfiguration(
                    task_definition=iqr_outlier_control_task,
                    initial_trigger=start_trigger,
                    child_task_fields={
                        quote_scope_field: wf.FieldMapping(map_from=quote_scope_field)  # pyright: ignore
                    },
                )
            ]
        ),
    )

    main_task_definition = wf.TaskDefinitionResource(
        id="import_quotes_task_definition",
        scope=deployment_name,
        code="ImportQuotes",
        display_name="Import Quotes",
        description="Import and validate quote data from specified Excel file.",
        states=[
            pending_state,
            wf.TaskStateDefinition(name="ImportingQuotes"),
            wf.TaskStateDefinition(name="InReasonableValueDQControl"),
            wf.TaskStateDefinition(name="InIQROutlierDQControl"),
            complete_state,
            wf.TaskStateDefinition(name="Error"),
        ],
        field_schema=[
            quote_scope_field,
            wf.TaskFieldDefinition(name="filename", type=wf.TaskFieldDefinitionType.STRING),
        ],
        initial_state=wf.InitialState(
            name=pending_state, required_fields=[quote_scope_field, "filename"]
        ),
        triggers=[
            start_trigger,
            wf.TriggerDefinition(name="Failure", type="External"),
            wf.TriggerDefinition(name="Imported", type="External"),
            resolved_trigger,
        ],
        transitions=[
            wf.TaskTransitionDefinition(
                from_state=pending_state,
                to_state="ImportingQuotes",
                trigger=start_trigger,
                action=start_import_action,
            ),
            wf.TaskTransitionDefinition(
                from_state="ImportingQuotes",
                to_state="InReasonableValueDQControl",
                trigger="Imported",
                action=create_reasonable_value_task_action,
            ),
            wf.TaskTransitionDefinition(
                from_state="InReasonableValueDQControl",
                to_state="InIQROutlierDQControl",
                trigger=resolved_trigger,
                action=create_iqr_outlier_task_action,
            ),
            wf.TaskTransitionDefinition(
                from_state="ImportingQuotes", to_state="Error", trigger="Failure"
            ),
            wf.TaskTransitionDefinition(
                from_state="InIQROutlierDQControl",
                to_state=complete_state,
                trigger=resolved_trigger,
                guard=f"childTasks all (state eq '{resolved_state.name}')",
            ),
        ],
        actions=[
            start_import_action,
            create_reasonable_value_task_action,
            create_iqr_outlier_task_action,
        ],
    )

    return Deployment(deployment_name, [main_task_definition])

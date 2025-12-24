from . import eps_dict
from . import ep
from inspect import getframeinfo, currentframe


def create_ep(ep_name):
	if ep_name == 'CREATE_MATRIX_FROM_TICKS':
		return ep.CreateMatrixFromTicks()
	if ep_name == 'VWAP':
		return ep.Vwap()
	if ep_name == 'SUM':
		return ep.Sum()
	if ep_name == 'CLOCK':
		return ep.Clock()
	if ep_name == 'HIGH':
		return ep.High()
	if ep_name == 'LOW':
		return ep.Low()
	if ep_name == 'FIRST':
		return ep.First()
	if ep_name == 'PRIMARY_EXCH':
		return ep.PrimaryExch()
	if ep_name == 'GENERIC_AGGREGATION':
		return ep.GenericAggregation()
	if ep_name == 'CORRELATION':
		return ep.Correlation()
	if ep_name == 'CORRELATION_BY_RANK':
		return ep.CorrelationByRank()
	if ep_name == 'FIRST_TICK':
		return ep.FirstTick()
	if ep_name == 'LAST':
		return ep.Last()
	if ep_name == 'FIRST_TIME':
		return ep.FirstTime()
	if ep_name == 'LAST_TIME':
		return ep.LastTime()
	if ep_name == 'LAST_TICK':
		return ep.LastTick()
	if ep_name == 'HIGH_TIME':
		return ep.HighTime()
	if ep_name == 'LOW_TIME':
		return ep.LowTime()
	if ep_name == 'HIGH_TICK':
		return ep.HighTick()
	if ep_name == 'LOW_TICK':
		return ep.LowTick()
	if ep_name == 'ORDER_BY_AGGR':
		return ep.OrderByAggr()
	if ep_name == 'NUM_TICKS':
		return ep.NumTicks()
	if ep_name == 'DUMP_TICK_SET':
		return ep.DumpTickSet()
	if ep_name == 'DUMP_TICK_LIST':
		return ep.DumpTickList()
	if ep_name == 'DUMP_TICK_DEQUE':
		return ep.DumpTickDeque()
	if ep_name == 'ESTIMATE_TS_DELAY':
		return ep.EstimateTsDelay()
	if ep_name == 'AVERAGE':
		return ep.Average()
	if ep_name == 'NUM_DISTINCT':
		return ep.NumDistinct()
	if ep_name == 'MEDIAN':
		return ep.Median()
	if ep_name == 'MULTI_PORTFOLIO_PRICE':
		return ep.MultiPortfolioPrice()
	if ep_name == 'VARIANCE':
		return ep.Variance()
	if ep_name == 'STDDEV':
		return ep.Stddev()
	if ep_name == 'STANDARDIZED_MOMENT':
		return ep.StandardizedMoment()
	if ep_name == 'RETURN':
		return ep.Return()
	if ep_name == 'PARTITION_EVENLY_INTO_GROUPS':
		return ep.PartitionEvenlyIntoGroups()
	if ep_name == 'PREVAILING_PRICE':
		return ep.PrevailingPrice()
	if ep_name == 'TW_AVERAGE':
		return ep.TwAverage()
	if ep_name == 'EXP_TW_AVERAGE':
		return ep.ExpTwAverage()
	if ep_name == 'EXP_W_AVERAGE':
		return ep.ExpWAverage()
	if ep_name == 'TW_SPREAD':
		return ep.TwSpread()
	if ep_name == 'OB_LOCK':
		return ep.ObLock()
	if ep_name == 'OB_SNAPSHOT':
		return ep.ObSnapshot()
	if ep_name == 'OB_SNAPSHOT_WIDE':
		return ep.ObSnapshotWide()
	if ep_name == 'OB_SNAPSHOT_FLAT':
		return ep.ObSnapshotFlat()
	if ep_name == 'DATA_SNAPSHOT':
		return ep.DataSnapshot()
	if ep_name == 'OB_SIZE':
		return ep.ObSize()
	if ep_name == 'OB_VWAP':
		return ep.ObVwap()
	if ep_name == 'ACCESS_INFO':
		return ep.AccessInfo()
	if ep_name == 'OB_NUM_LEVELS':
		return ep.ObNumLevels()
	if ep_name == 'OB_SUMMARY':
		return ep.ObSummary()
	if ep_name == 'PORTFOLIO_PRICE':
		return ep.PortfolioPrice()
	if ep_name == 'OPTION_PRICE':
		return ep.OptionPrice()
	if ep_name == 'IMPLIED_VOL':
		return ep.ImpliedVol()
	if ep_name == 'MERGE':
		return ep.Merge()
	if ep_name == 'TS_ADD':
		return ep.TsAdd()
	if ep_name == 'DB/SHOW_CORRECTION_STATUS':
		return ep.DbShowCorrectionStatus()
	if ep_name == 'TS_SUBTRACT':
		return ep.TsSubtract()
	if ep_name == 'SHOW_COMPRESSED_FILE_CONTENT':
		return ep.ShowCompressedFileContent()
	if ep_name == 'CSV_FILE_LISTING':
		return ep.CsvFileListing()
	if ep_name == 'CSV_FILE_QUERY':
		return ep.CsvFileQuery()
	if ep_name == 'LINEAR_REGRESSION':
		return ep.LinearRegression()
	if ep_name == 'DATA_FILE_QUERY':
		return ep.DataFileQuery()
	if ep_name == 'READ_FROM_PARQUET':
		return ep.ReadFromParquet()
	if ep_name == 'WRITE_TO_PARQUET':
		return ep.WriteToParquet()
	if ep_name == 'COMMAND_EXECUTE':
		return ep.CommandExecute()
	if ep_name == 'DIRECTORY_LISTING':
		return ep.DirectoryListing()
	if ep_name == 'OTQ_QUERY':
		return ep.OtqQuery()
	if ep_name == 'CEP_SIMULATOR':
		return ep.CepSimulator()
	if ep_name == 'SPLIT_QUERY_OUTPUT_BY_SYMBOL':
		return ep.SplitQueryOutputBySymbol()
	if ep_name == 'POINT_IN_TIME':
		return ep.PointInTime()
	if ep_name == 'NESTED_OTQ':
		return ep.NestedOtq()
	if ep_name == 'OMD::WRITE_TO_KAFKA':
		return ep.Omd_writeToKafka()
	if ep_name == 'OTQ_PLACEHOLDER':
		return ep.OtqPlaceholder()
	if ep_name == 'GROUP_BY':
		return ep.GroupBy()
	if ep_name == 'SWITCH_SYMBOLS_AND_THREADS':
		return ep.SwitchSymbolsAndThreads()
	if ep_name == 'MODIFY_TS_FIELD_PROPERTIES':
		return ep.ModifyTsFieldProperties()
	if ep_name == 'QUERY_SYMBOLS':
		return ep.QuerySymbols()
	if ep_name == 'MEMORY_USAGE':
		return ep.MemoryUsage()
	if ep_name == 'DECLARE_STATE_VARIABLES':
		return ep.DeclareStateVariables()
	if ep_name == 'TS_EXPRESSION':
		return ep.TsExpression()
	if ep_name == 'MODIFY_STATE_VAR_FROM_QUERY':
		return ep.ModifyStateVarFromQuery()
	if ep_name == 'PASSTHROUGH':
		return ep.Passthrough()
	if ep_name == 'PREPEND_INITIAL_STATE':
		return ep.PrependInitialState()
	if ep_name == 'TABLE':
		return ep.Table()
	if ep_name == 'CREATE_TICK_BLOCKS':
		return ep.CreateTickBlocks()
	if ep_name == 'RENAME_FIELDS':
		return ep.RenameFields()
	if ep_name == 'REPLICATE':
		return ep.Replicate()
	if ep_name == 'MODIFY_SYMBOL_NAME':
		return ep.ModifySymbolName()
	if ep_name == 'MERGE_NONBOUND_SYMBOLS':
		return ep.MergeNonboundSymbols()
	if ep_name == 'DB/RENAME_FIELD':
		return ep.DbRenameField()
	if ep_name == 'SYNCHRONIZE_TIME':
		return ep.SynchronizeTime()
	if ep_name == 'ML::DLIB_BINARY_CLASSIFY_TRAIN_RVM_WITH_RADIAL_BASIS_KERNEL':
		return ep.Ml_dlibBinaryClassifyTrainRvmWithRadialBasisKernel()
	if ep_name == 'COALESCE':
		return ep.Coalesce()
	if ep_name == 'WHERE_CLAUSE':
		return ep.WhereClause()
	if ep_name == 'PRESORT':
		return ep.Presort()
	if ep_name == 'SYNCHRONIZE_TIME_ACROSS_SYMBOLS':
		return ep.SynchronizeTimeAcrossSymbols()
	if ep_name == 'JOIN':
		return ep.Join()
	if ep_name == 'JOIN_SAME_SIZE_TS':
		return ep.JoinSameSizeTs()
	if ep_name == 'TRD_QUOTE_JOIN':
		return ep.TrdQuoteJoin()
	if ep_name == 'TRD_OB_JOIN':
		return ep.TrdObJoin()
	if ep_name == 'DB/INSERT_ROW':
		return ep.DbInsertRow()
	if ep_name == 'JOIN_BY_TIME':
		return ep.JoinByTime()
	if ep_name == 'JOIN_WITH_QUERY':
		return ep.JoinWithQuery()
	if ep_name == 'JOIN_WITH_COLLECTION_SUMMARY':
		return ep.JoinWithCollectionSummary()
	if ep_name == 'UPDATE_TICK_SETS':
		return ep.UpdateTickSets()
	if ep_name == 'UPDATE_FROM_TICK_SET':
		return ep.UpdateFromTickSet()
	if ep_name == 'ML::DLIB_REGRESSION_PREDICT':
		return ep.Ml_dlibRegressionPredict()
	if ep_name == 'TRANSPOSE':
		return ep.Transpose()
	if ep_name == 'VIRTUAL_OB':
		return ep.VirtualOb()
	if ep_name == 'BOOK_DIFF':
		return ep.BookDiff()
	if ep_name == 'DISTINCT':
		return ep.Distinct()
	if ep_name == 'INSERT_TICK':
		return ep.InsertTick()
	if ep_name == 'INSERT_DATA_QUALITY_EVENT':
		return ep.InsertDataQualityEvent()
	if ep_name == 'INSERT_HEARTBEAT':
		return ep.InsertHeartbeat()
	if ep_name == 'CREATE_TICKS_FROM_MATRIX':
		return ep.CreateTicksFromMatrix()
	if ep_name == 'SAVE_SNAPSHOT':
		return ep.SaveSnapshot()
	if ep_name == 'READ_SNAPSHOT':
		return ep.ReadSnapshot()
	if ep_name == 'SHOW_SNAPSHOT_LIST':
		return ep.ShowSnapshotList()
	if ep_name == 'JOIN_WITH_SNAPSHOT':
		return ep.JoinWithSnapshot()
	if ep_name == 'DIFF':
		return ep.Diff()
	if ep_name == 'WRITE_TO_RAW':
		return ep.WriteToRaw()
	if ep_name == 'PAUSE':
		return ep.Pause()
	if ep_name == 'THROW':
		return ep.Throw()
	if ep_name == 'NAMED_QUEUE_READER':
		return ep.NamedQueueReader()
	if ep_name == 'MODIFY_TS_PROPERTIES':
		return ep.ModifyTsProperties()
	if ep_name == 'INSERT_AT_END':
		return ep.InsertAtEnd()
	if ep_name == 'EXECUTE_OTQ_RECURSIVELY':
		return ep.ExecuteOtqRecursively()
	if ep_name == 'CREATE_TICK_FROM_FID_VALS':
		return ep.CreateTickFromFidVals()
	if ep_name == 'FID_VAL_FILE_ANALYZER':
		return ep.FidValFileAnalyzer()
	if ep_name == 'PNL_REALIZED':
		return ep.PnlRealized()
	if ep_name == 'JOIN_WITH_AGGREGATED_WINDOW':
		return ep.JoinWithAggregatedWindow()
	if ep_name == 'RESOLVE_ENUMS':
		return ep.ResolveEnums()
	if ep_name == 'ENCODING_CONVERTER':
		return ep.EncodingConverter()
	if ep_name == 'OM::MATCHING_ENGINE_INITIAL_STATE':
		return ep.Om_matchingEngineInitialState()
	if ep_name == 'CODE':
		return ep.Code()
	if ep_name == 'SHOW_CORRECTED_TICKS':
		return ep.ShowCorrectedTicks()
	if ep_name == 'SHOW_DATA_QUALITY':
		return ep.ShowDataQuality()
	if ep_name == 'SHOW_SYMBOL_ERRORS':
		return ep.ShowSymbolErrors()
	if ep_name == 'SHOW_HEARTBEATS':
		return ep.ShowHeartbeats()
	if ep_name == 'SHOW_SPECIAL_MSGS':
		return ep.ShowSpecialMsgs()
	if ep_name == 'SHOW_TICK_DESCRIPTOR':
		return ep.ShowTickDescriptor()
	if ep_name == 'DB/SHOW_LAST_TICK_DESCRIPTOR':
		return ep.DbShowLastTickDescriptor()
	if ep_name == 'MKT_ACTIVITY':
		return ep.MktActivity()
	if ep_name == 'DB/SHOW_TICK_TYPES':
		return ep.DbShowTickTypes()
	if ep_name == 'SHOW_HIDDEN_TICKS':
		return ep.ShowHiddenTicks()
	if ep_name == 'HIDE_TICKS_WITH_STATUS':
		return ep.HideTicksWithStatus()
	if ep_name == 'SHOW_INITIALIZATION_TICKS':
		return ep.ShowInitializationTicks()
	if ep_name == 'MID':
		return ep.Mid()
	if ep_name == 'ADD_FIELD':
		return ep.AddField()
	if ep_name == 'ADD_FIELDS':
		return ep.AddFields()
	if ep_name == 'ADD_FIELDS_FROM_SYMBOL_PARAMS':
		return ep.AddFieldsFromSymbolParams()
	if ep_name == 'PERCENTILE':
		return ep.Percentile()
	if ep_name == 'ML::BINARY_CLASSIFY_PERF_EVALUATOR':
		return ep.Ml_binaryClassifyPerfEvaluator()
	if ep_name == 'TEXT/DETECT_CATEGORY':
		return ep.TextDetectCategory()
	if ep_name == 'UPDATE_FIELD':
		return ep.UpdateField()
	if ep_name == 'UPDATE_FIELDS':
		return ep.UpdateFields()
	if ep_name == 'EXECUTE_EXPRESSIONS':
		return ep.ExecuteExpressions()
	if ep_name == 'UPDATE_TIMESTAMP':
		return ep.UpdateTimestamp()
	if ep_name == 'MODIFY_QUERY_TIMES':
		return ep.ModifyQueryTimes()
	if ep_name == 'HELPER/FIX_BOOK_EXCH_TIME':
		return ep.HelperFixBookExchTime()
	if ep_name == 'INTERCEPT_HEARTBEATS':
		return ep.InterceptHeartbeats()
	if ep_name == 'INTERCEPT_DATA_QUALITY':
		return ep.InterceptDataQuality()
	if ep_name == 'INTERCEPT_SYMBOL_ERRORS':
		return ep.InterceptSymbolErrors()
	if ep_name == 'INTERCEPT_INITIALIZATION_TICKS':
		return ep.InterceptInitializationTicks()
	if ep_name == 'CORRECT_TICK_FILTER':
		return ep.CorrectTickFilter()
	if ep_name == 'OM::MATCHING_ENGINE_SIMPLE':
		return ep.Om_matchingEngineSimple()
	if ep_name == 'TRD_VS_MID':
		return ep.TrdVsMid()
	if ep_name == 'TRD_VS_QUOTE':
		return ep.TrdVsQuote()
	if ep_name == 'LEE_AND_READY':
		return ep.LeeAndReady()
	if ep_name == 'FORMAT_TICK':
		return ep.FormatTick()
	if ep_name == 'UPTICK':
		return ep.Uptick()
	if ep_name == 'VALUE_COMPARE':
		return ep.ValueCompare()
	if ep_name == 'REGEX_MATCHES':
		return ep.RegexMatches()
	if ep_name == 'TIME_FILTER':
		return ep.TimeFilter()
	if ep_name == 'CHARACTER_PRESENT':
		return ep.CharacterPresent()
	if ep_name == 'BYTE_PRESENT':
		return ep.BytePresent()
	if ep_name == 'VALUE_PRESENT':
		return ep.ValuePresent()
	if ep_name == 'OM/BACKTESTING_MANAGER':
		return ep.OmBacktestingManager()
	if ep_name == 'VOLUME_LIMIT':
		return ep.VolumeLimit()
	if ep_name == 'SKIP_BAD_TICK':
		return ep.SkipBadTick()
	if ep_name == 'LIMIT':
		return ep.Limit()
	if ep_name == 'INTERPOLATE':
		return ep.Interpolate()
	if ep_name == 'SWITCH':
		return ep.Switch()
	if ep_name == 'ORDER_BY':
		return ep.OrderBy()
	if ep_name == 'RANKING':
		return ep.Ranking()
	if ep_name == 'FIND_VALUE_FOR_PERCENTILE':
		return ep.FindValueForPercentile()
	if ep_name == 'FIND_VALUES_FOR_PERCENTILES':
		return ep.FindValuesForPercentiles()
	if ep_name == 'COMPUTE':
		return ep.Compute()
	if ep_name == 'SHOW_SYMBOL_NAME_IN_DB':
		return ep.ShowSymbolNameInDb()
	if ep_name == 'STOP_QUERY':
		return ep.StopQuery()
	if ep_name == 'SHOW_OTQ_LIST':
		return ep.ShowOtqList()
	if ep_name == 'WRITE_TO_ONETICK_DB':
		return ep.WriteToOnetickDb()
	if ep_name == 'READ_FROM_RAW':
		return ep.ReadFromRaw()
	if ep_name == 'TICK_GENERATOR':
		return ep.TickGenerator()
	if ep_name == 'ML::REGRESSION_PERF_EVALUATOR':
		return ep.Ml_regressionPerfEvaluator()
	if ep_name == 'SHOW_HOSTS_FOR_DBS':
		return ep.ShowHostsForDbs()
	if ep_name == 'SET_APPLICATION_NAME':
		return ep.SetApplicationName()
	if ep_name == 'CORP_ACTIONS':
		return ep.CorpActions()
	if ep_name == 'DB/DELETE':
		return ep.DbDelete()
	if ep_name == 'DB/INSERT_DATA_QUALITY_EVENT':
		return ep.DbInsertDataQualityEvent()
	if ep_name == 'DB/RENAME_TICK_TYPE':
		return ep.DbRenameTickType()
	if ep_name == 'DB/RENAME_SYMBOL':
		return ep.DbRenameSymbol()
	if ep_name == 'DB/SHOW_LOADED_TIME_RANGES':
		return ep.DbShowLoadedTimeRanges()
	if ep_name == 'DB/UPDATE':
		return ep.DbUpdate()
	if ep_name == 'DISK_USAGE':
		return ep.DiskUsage()
	if ep_name == 'FIND_DB_SYMBOLS':
		return ep.FindDbSymbols()
	if ep_name == 'FIND_SNAPSHOT_SYMBOLS':
		return ep.FindSnapshotSymbols()
	if ep_name == 'FX_CONVERTER':
		return ep.FxConverter()
	if ep_name == 'MODIFY_ACCESS_CONTROL':
		return ep.ModifyAccessControl()
	if ep_name == 'REF_DATA':
		return ep.RefData()
	if ep_name == 'SHOW_TICK_DESCRIPTOR_IN_DB':
		return ep.ShowTickDescriptorInDb()
	if ep_name == 'SHOW_OT_ENTITLEMENTS':
		return ep.ShowOtEntitlements()
	if ep_name == 'SHOW_QUERY_PROPERTIES':
		return ep.ShowQueryProperties()
	if ep_name == 'SHOW_ARCHIVE_STATS':
		return ep.ShowArchiveStats()
	if ep_name == 'SYMBOLOGY_MAPPING':
		return ep.SymbologyMapping()
	if ep_name == 'WRITE_TEXT':
		return ep.WriteText()
	if ep_name == 'OMD::WRITE_TO_SOLACE':
		return ep.Omd_writeToSolace()
	if ep_name == 'DB/SHOW_CONFIG':
		return ep.DbShowConfig()
	if ep_name == 'CREATE_CACHE':
		return ep.CreateCache()
	if ep_name == 'READ_CACHE':
		return ep.ReadCache()
	if ep_name == 'DELETE_CACHE':
		return ep.DeleteCache()
	if ep_name == 'MODIFY_CACHE_CONFIG':
		return ep.ModifyCacheConfig()
	if ep_name == 'LICENSE/EXPORTING_CORES_INFO':
		return ep.LicenseExportingCoresInfo()
	if ep_name == 'SHOW_EP_LIST':
		return ep.ShowEpList()
	if ep_name == 'SHOW_EP_INFO':
		return ep.ShowEpInfo()
	if ep_name == 'SHOW_FUNCTION_LIST':
		return ep.ShowFunctionList()
	if ep_name == 'SHOW_DB_LIST':
		return ep.ShowDbList()
	if ep_name == 'SHOW_SYMBOLOGY_LIST':
		return ep.ShowSymbologyList()
	if ep_name == 'DB/SHOW_REALTIME_STATS':
		return ep.DbShowRealtimeStats()
	if ep_name == 'RELOAD_CONFIG':
		return ep.ReloadConfig()
	if ep_name == 'SHOW_ACTIVE_QUERY_LIST':
		return ep.ShowActiveQueryList()
	if ep_name == 'PER_TICK_SCRIPT':
		return ep.PerTickScript()
	if ep_name == 'SHOW_QUERIES_IN_SERVER_QUEUE':
		return ep.ShowQueriesInServerQueue()
	if ep_name == 'EXECUTE_ON_REMOTE_HOST':
		return ep.ExecuteOnRemoteHost()
	if ep_name == 'SHUTDOWN_CEP_ADAPTER':
		return ep.ShutdownCepAdapter()
	if ep_name == 'DB/SHOW_CONFIGURED_TIME_RANGES':
		return ep.DbShowConfiguredTimeRanges()
	if ep_name == 'DB/DESTROY':
		return ep.DbDestroy()
	if ep_name == 'SHOW_DERIVED_DB_LIST':
		return ep.ShowDerivedDbList()
	if ep_name == 'SHOW_QUERY_FROM_LOG':
		return ep.ShowQueryFromLog()
	if ep_name == 'DB/GET_SYMBOL_OFFSETS':
		return ep.DbGetSymbolOffsets()
	if ep_name == 'CAPTURE_REPLAY_OT_EVENTS':
		return ep.CaptureReplayOtEvents()
	if ep_name == 'SCHEDULER/GET_EXECUTORS':
		return ep.SchedulerGetExecutors()
	if ep_name == 'START_QUERY_ON_SERVER':
		return ep.StartQueryOnServer()
	if ep_name == 'TRY_CATCH':
		return ep.TryCatch()
	if ep_name == 'DB/SHOW_DEFAULT_TICK_TYPES':
		return ep.DbShowDefaultTickTypes()
	if ep_name == 'DB/MODIFY_DEFAULT_TICK_TYPES':
		return ep.DbModifyDefaultTickTypes()
	if ep_name == 'OM::WALLET_MANAGER':
		return ep.Om_walletManager()
	if ep_name == 'OM::WALLET_MANAGER_FEEDBACK':
		return ep.Om_walletManagerFeedback()
	if ep_name == 'OM/STRATEGY_INSTANCE_MANAGER':
		return ep.OmStrategyInstanceManager()
	if ep_name == 'OM/STRATEGY_DB_MANAGER':
		return ep.OmStrategyDbManager()
	if ep_name == 'OM/ORDER_PROCESSOR':
		return ep.OmOrderProcessor()
	if ep_name == 'OM/STATISTICS':
		return ep.OmStatistics()
	if ep_name == 'OM/RETRIEVE_ORDER_DATA':
		return ep.OmRetrieveOrderData()
	if ep_name == 'MR/RUN_MAP_TASK':
		return ep.MrRunMapTask()
	if ep_name == 'OMD::WRITE_TO_AMQP':
		return ep.Omd_writeToAmqp()
	if ep_name == 'OMD::ODBC_QUERY':
		return ep.Omd_odbcQuery()
	if ep_name == 'OMD::WRITE_TO_ODBC':
		return ep.Omd_writeToOdbc()
	if ep_name == 'OMD::WRITE_TO_SMTP':
		return ep.Omd_writeToSmtp()
	if ep_name == 'ML::DLIB_BINARY_CLASSIFY_TRAIN_SVM_C_WITH_RADIAL_BASIS_KERNEL':
		return ep.Ml_dlibBinaryClassifyTrainSvmCWithRadialBasisKernel()
	if ep_name == 'ML::DLIB_BINARY_CLASSIFY_TRAIN_KRR_WITH_RADIAL_BASIS_KERNEL':
		return ep.Ml_dlibBinaryClassifyTrainKrrWithRadialBasisKernel()
	if ep_name == 'ML::DLIB_BINARY_CLASSIFY_PREDICT':
		return ep.Ml_dlibBinaryClassifyPredict()
	if ep_name == 'ML::DLIB_REGRESSION_TRAIN_KRR_WITH_RADIAL_BASIS_KERNEL':
		return ep.Ml_dlibRegressionTrainKrrWithRadialBasisKernel()
	if ep_name == 'ML::DLIB_REGRESSION_TRAIN_SVR_WITH_RADIAL_BASIS_KERNEL':
		return ep.Ml_dlibRegressionTrainSvrWithRadialBasisKernel()
	if ep_name == 'ML::DLIB_BINARY_CLASSIFY_STREAM_SVM_PEGASOS_WITH_RADIAL_BASIS_KERNEL':
		return ep.Ml_dlibBinaryClassifyStreamSvmPegasosWithRadialBasisKernel()
	if ep_name == 'ML::DLIB_REGRESSION_STREAM_KRLS_WITH_RADIAL_BASIS_KERNEL':
		return ep.Ml_dlibRegressionStreamKrlsWithRadialBasisKernel()
	if ep_name == 'ML::DLIB_REGRESSION_STREAM_RLS':
		return ep.Ml_dlibRegressionStreamRls()
	if ep_name == 'ML::DLIB_CLUSTERING_K_MEANS_WITH_RADIAL_BASIS_KERNEL':
		return ep.Ml_dlibClusteringKMeansWithRadialBasisKernel()
	if ep_name == 'OMD::READ_FROM_URL':
		return ep.Omd_readFromUrl()
	if ep_name in eps_dict:
		return eps_dict[ep_name]()

	raise Exception('wrong ep name: {}.'.format(ep_name), getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno)

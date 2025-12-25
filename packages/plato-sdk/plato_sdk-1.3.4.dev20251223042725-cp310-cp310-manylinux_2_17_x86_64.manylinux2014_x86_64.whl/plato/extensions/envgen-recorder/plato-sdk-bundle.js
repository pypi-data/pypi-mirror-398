var PlatoSDK = (() => {
  var __defProp = Object.defineProperty;
  var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
  var __getOwnPropNames = Object.getOwnPropertyNames;
  var __hasOwnProp = Object.prototype.hasOwnProperty;
  var __defNormalProp = (obj, key, value) => key in obj ? __defProp(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
  var __export = (target, all) => {
    for (var name in all)
      __defProp(target, name, { get: all[name], enumerable: true });
  };
  var __copyProps = (to, from, except, desc) => {
    if (from && typeof from === "object" || typeof from === "function") {
      for (let key of __getOwnPropNames(from))
        if (!__hasOwnProp.call(to, key) && key !== except)
          __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
    }
    return to;
  };
  var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);
  var __publicField = (obj, key, value) => __defNormalProp(obj, typeof key !== "symbol" ? key + "" : key, value);

  // sdk-browser-entry.ts
  var sdk_browser_entry_exports = {};
  __export(sdk_browser_entry_exports, {
    AuthenticationFromJSON: () => AuthenticationFromJSON,
    AuthenticationFromJSONTyped: () => AuthenticationFromJSONTyped,
    AuthenticationToJSON: () => AuthenticationToJSON,
    AuthenticationToJSONTyped: () => AuthenticationToJSONTyped,
    BASE_PATH: () => BASE_PATH,
    BaseAPI: () => BaseAPI,
    BaseScoringConfigFromJSON: () => BaseScoringConfigFromJSON,
    BaseScoringConfigFromJSONTyped: () => BaseScoringConfigFromJSONTyped,
    BaseScoringConfigToJSON: () => BaseScoringConfigToJSON,
    BaseScoringConfigToJSONTyped: () => BaseScoringConfigToJSONTyped,
    BaseScoringConfigTypeEnum: () => BaseScoringConfigTypeEnum,
    BaseStructuredRunLogFromJSON: () => BaseStructuredRunLogFromJSON,
    BaseStructuredRunLogFromJSONTyped: () => BaseStructuredRunLogFromJSONTyped,
    BaseStructuredRunLogSourceEnum: () => BaseStructuredRunLogSourceEnum,
    BaseStructuredRunLogToJSON: () => BaseStructuredRunLogToJSON,
    BaseStructuredRunLogToJSONTyped: () => BaseStructuredRunLogToJSONTyped,
    BaseStructuredRunLogTypeEnum: () => BaseStructuredRunLogTypeEnum,
    BatchLogRequestFromJSON: () => BatchLogRequestFromJSON,
    BatchLogRequestFromJSONTyped: () => BatchLogRequestFromJSONTyped,
    BatchLogRequestToJSON: () => BatchLogRequestToJSON,
    BatchLogRequestToJSONTyped: () => BatchLogRequestToJSONTyped,
    BlobApiResponse: () => BlobApiResponse,
    COLLECTION_FORMATS: () => COLLECTION_FORMATS,
    ChromeCookieFromJSON: () => ChromeCookieFromJSON,
    ChromeCookieFromJSONTyped: () => ChromeCookieFromJSONTyped,
    ChromeCookieToJSON: () => ChromeCookieToJSON,
    ChromeCookieToJSONTyped: () => ChromeCookieToJSONTyped,
    Configuration: () => Configuration,
    CreateSimulatorRequestFromJSON: () => CreateSimulatorRequestFromJSON,
    CreateSimulatorRequestFromJSONTyped: () => CreateSimulatorRequestFromJSONTyped,
    CreateSimulatorRequestToJSON: () => CreateSimulatorRequestToJSON,
    CreateSimulatorRequestToJSONTyped: () => CreateSimulatorRequestToJSONTyped,
    CreateSnapshotRequestFromJSON: () => CreateSnapshotRequestFromJSON,
    CreateSnapshotRequestFromJSONTyped: () => CreateSnapshotRequestFromJSONTyped,
    CreateSnapshotRequestToJSON: () => CreateSnapshotRequestToJSON,
    CreateSnapshotRequestToJSONTyped: () => CreateSnapshotRequestToJSONTyped,
    CreateSnapshotResponseFromJSON: () => CreateSnapshotResponseFromJSON,
    CreateSnapshotResponseFromJSONTyped: () => CreateSnapshotResponseFromJSONTyped,
    CreateSnapshotResponseToJSON: () => CreateSnapshotResponseToJSON,
    CreateSnapshotResponseToJSONTyped: () => CreateSnapshotResponseToJSONTyped,
    CreateVMRequestFromJSON: () => CreateVMRequestFromJSON,
    CreateVMRequestFromJSONTyped: () => CreateVMRequestFromJSONTyped,
    CreateVMRequestToJSON: () => CreateVMRequestToJSON,
    CreateVMRequestToJSONTyped: () => CreateVMRequestToJSONTyped,
    CreateVMResponseFromJSON: () => CreateVMResponseFromJSON,
    CreateVMResponseFromJSONTyped: () => CreateVMResponseFromJSONTyped,
    CreateVMResponseToJSON: () => CreateVMResponseToJSON,
    CreateVMResponseToJSONTyped: () => CreateVMResponseToJSONTyped,
    DbConfigResponseFromJSON: () => DbConfigResponseFromJSON,
    DbConfigResponseFromJSONTyped: () => DbConfigResponseFromJSONTyped,
    DbConfigResponseToJSON: () => DbConfigResponseToJSON,
    DbConfigResponseToJSONTyped: () => DbConfigResponseToJSONTyped,
    DefaultConfig: () => DefaultConfig,
    EnvApi: () => EnvApi,
    EvaluateRequestFromJSON: () => EvaluateRequestFromJSON,
    EvaluateRequestFromJSONTyped: () => EvaluateRequestFromJSONTyped,
    EvaluateRequestToJSON: () => EvaluateRequestToJSON,
    EvaluateRequestToJSONTyped: () => EvaluateRequestToJSONTyped,
    FetchError: () => FetchError,
    GetOperationEvents200ResponseFromJSON: () => GetOperationEvents200ResponseFromJSON,
    GetOperationEvents200ResponseFromJSONTyped: () => GetOperationEvents200ResponseFromJSONTyped,
    GetOperationEvents200ResponseToJSON: () => GetOperationEvents200ResponseToJSON,
    GetOperationEvents200ResponseToJSONTyped: () => GetOperationEvents200ResponseToJSONTyped,
    GetOperationEvents200ResponseTypeEnum: () => GetOperationEvents200ResponseTypeEnum,
    GetOperationEventsApiPublicBuildEventsCorrelationIdGet200ResponseFromJSON: () => GetOperationEventsApiPublicBuildEventsCorrelationIdGet200ResponseFromJSON,
    GetOperationEventsApiPublicBuildEventsCorrelationIdGet200ResponseFromJSONTyped: () => GetOperationEventsApiPublicBuildEventsCorrelationIdGet200ResponseFromJSONTyped,
    GetOperationEventsApiPublicBuildEventsCorrelationIdGet200ResponseToJSON: () => GetOperationEventsApiPublicBuildEventsCorrelationIdGet200ResponseToJSON,
    GetOperationEventsApiPublicBuildEventsCorrelationIdGet200ResponseToJSONTyped: () => GetOperationEventsApiPublicBuildEventsCorrelationIdGet200ResponseToJSONTyped,
    GetOperationEventsApiPublicBuildEventsCorrelationIdGet200ResponseTypeEnum: () => GetOperationEventsApiPublicBuildEventsCorrelationIdGet200ResponseTypeEnum,
    GiteaApi: () => GiteaApi,
    HTTPValidationErrorFromJSON: () => HTTPValidationErrorFromJSON,
    HTTPValidationErrorFromJSONTyped: () => HTTPValidationErrorFromJSONTyped,
    HTTPValidationErrorToJSON: () => HTTPValidationErrorToJSON,
    HTTPValidationErrorToJSONTyped: () => HTTPValidationErrorToJSONTyped,
    JSONApiResponse: () => JSONApiResponse,
    JobStatusResponseFromJSON: () => JobStatusResponseFromJSON,
    JobStatusResponseFromJSONTyped: () => JobStatusResponseFromJSONTyped,
    JobStatusResponseToJSON: () => JobStatusResponseToJSON,
    JobStatusResponseToJSONTyped: () => JobStatusResponseToJSONTyped,
    LocationInnerFromJSON: () => LocationInnerFromJSON,
    LocationInnerFromJSONTyped: () => LocationInnerFromJSONTyped,
    LocationInnerToJSON: () => LocationInnerToJSON,
    LocationInnerToJSONTyped: () => LocationInnerToJSONTyped,
    LogFromJSON: () => LogFromJSON,
    LogFromJSONTyped: () => LogFromJSONTyped,
    LogToJSON: () => LogToJSON,
    LogToJSONTyped: () => LogToJSONTyped,
    MakeEnvRequest2FromJSON: () => MakeEnvRequest2FromJSON,
    MakeEnvRequest2FromJSONTyped: () => MakeEnvRequest2FromJSONTyped,
    MakeEnvRequest2InterfaceTypeEnum: () => MakeEnvRequest2InterfaceTypeEnum,
    MakeEnvRequest2ToJSON: () => MakeEnvRequest2ToJSON,
    MakeEnvRequest2ToJSONTyped: () => MakeEnvRequest2ToJSONTyped,
    MakeEnvResponseFromJSON: () => MakeEnvResponseFromJSON,
    MakeEnvResponseFromJSONTyped: () => MakeEnvResponseFromJSONTyped,
    MakeEnvResponseToJSON: () => MakeEnvResponseToJSON,
    MakeEnvResponseToJSONTyped: () => MakeEnvResponseToJSONTyped,
    OperationFailedError: () => OperationFailedError,
    OperationTimeoutError: () => OperationTimeoutError,
    PlatoClient: () => PlatoClient,
    PublicBuildApi: () => PublicBuildApi,
    RequiredError: () => RequiredError,
    ResetEnvRequestFromJSON: () => ResetEnvRequestFromJSON,
    ResetEnvRequestFromJSONTyped: () => ResetEnvRequestFromJSONTyped,
    ResetEnvRequestToJSON: () => ResetEnvRequestToJSON,
    ResetEnvRequestToJSONTyped: () => ResetEnvRequestToJSONTyped,
    ResetEnvTaskFromJSON: () => ResetEnvTaskFromJSON,
    ResetEnvTaskFromJSONTyped: () => ResetEnvTaskFromJSONTyped,
    ResetEnvTaskToJSON: () => ResetEnvTaskToJSON,
    ResetEnvTaskToJSONTyped: () => ResetEnvTaskToJSONTyped,
    ResponseError: () => ResponseError,
    ScoreRequestFromJSON: () => ScoreRequestFromJSON,
    ScoreRequestFromJSONTyped: () => ScoreRequestFromJSONTyped,
    ScoreRequestToJSON: () => ScoreRequestToJSON,
    ScoreRequestToJSONTyped: () => ScoreRequestToJSONTyped,
    SetupRootPasswordRequestFromJSON: () => SetupRootPasswordRequestFromJSON,
    SetupRootPasswordRequestFromJSONTyped: () => SetupRootPasswordRequestFromJSONTyped,
    SetupRootPasswordRequestToJSON: () => SetupRootPasswordRequestToJSON,
    SetupRootPasswordRequestToJSONTyped: () => SetupRootPasswordRequestToJSONTyped,
    SetupSandboxRequestFromJSON: () => SetupSandboxRequestFromJSON,
    SetupSandboxRequestFromJSONTyped: () => SetupSandboxRequestFromJSONTyped,
    SetupSandboxRequestToJSON: () => SetupSandboxRequestToJSON,
    SetupSandboxRequestToJSONTyped: () => SetupSandboxRequestToJSONTyped,
    SetupSandboxResponseFromJSON: () => SetupSandboxResponseFromJSON,
    SetupSandboxResponseFromJSONTyped: () => SetupSandboxResponseFromJSONTyped,
    SetupSandboxResponseToJSON: () => SetupSandboxResponseToJSON,
    SetupSandboxResponseToJSONTyped: () => SetupSandboxResponseToJSONTyped,
    SimConfigComputeFromJSON: () => SimConfigComputeFromJSON,
    SimConfigComputeFromJSONTyped: () => SimConfigComputeFromJSONTyped,
    SimConfigComputeToJSON: () => SimConfigComputeToJSON,
    SimConfigComputeToJSONTyped: () => SimConfigComputeToJSONTyped,
    SimConfigDatasetFromJSON: () => SimConfigDatasetFromJSON,
    SimConfigDatasetFromJSONTyped: () => SimConfigDatasetFromJSONTyped,
    SimConfigDatasetToJSON: () => SimConfigDatasetToJSON,
    SimConfigDatasetToJSONTyped: () => SimConfigDatasetToJSONTyped,
    SimConfigListenerFromJSON: () => SimConfigListenerFromJSON,
    SimConfigListenerFromJSONTyped: () => SimConfigListenerFromJSONTyped,
    SimConfigListenerToJSON: () => SimConfigListenerToJSON,
    SimConfigListenerToJSONTyped: () => SimConfigListenerToJSONTyped,
    SimConfigListenerTypeEnum: () => SimConfigListenerTypeEnum,
    SimConfigMetadataFromJSON: () => SimConfigMetadataFromJSON,
    SimConfigMetadataFromJSONTyped: () => SimConfigMetadataFromJSONTyped,
    SimConfigMetadataToJSON: () => SimConfigMetadataToJSON,
    SimConfigMetadataToJSONTyped: () => SimConfigMetadataToJSONTyped,
    SimConfigServiceFromJSON: () => SimConfigServiceFromJSON,
    SimConfigServiceFromJSONTyped: () => SimConfigServiceFromJSONTyped,
    SimConfigServiceToJSON: () => SimConfigServiceToJSON,
    SimConfigServiceToJSONTyped: () => SimConfigServiceToJSONTyped,
    SimConfigServiceTypeEnum: () => SimConfigServiceTypeEnum,
    SimStatusHistoryFromJSON: () => SimStatusHistoryFromJSON,
    SimStatusHistoryFromJSONTyped: () => SimStatusHistoryFromJSONTyped,
    SimStatusHistoryToJSON: () => SimStatusHistoryToJSON,
    SimStatusHistoryToJSONTyped: () => SimStatusHistoryToJSONTyped,
    SimulatorApi: () => SimulatorApi,
    SimulatorConfigFromJSON: () => SimulatorConfigFromJSON,
    SimulatorConfigFromJSONTyped: () => SimulatorConfigFromJSONTyped,
    SimulatorConfigStatusEnum: () => SimulatorConfigStatusEnum,
    SimulatorConfigToJSON: () => SimulatorConfigToJSON,
    SimulatorConfigToJSONTyped: () => SimulatorConfigToJSONTyped,
    SimulatorConfigTypeEnum: () => SimulatorConfigTypeEnum,
    SimulatorListItemFromJSON: () => SimulatorListItemFromJSON,
    SimulatorListItemFromJSONTyped: () => SimulatorListItemFromJSONTyped,
    SimulatorListItemToJSON: () => SimulatorListItemToJSON,
    SimulatorListItemToJSONTyped: () => SimulatorListItemToJSONTyped,
    SimulatorStatusFromJSON: () => SimulatorStatusFromJSON,
    SimulatorStatusFromJSONTyped: () => SimulatorStatusFromJSONTyped,
    SimulatorStatusToJSON: () => SimulatorStatusToJSON,
    SimulatorStatusToJSONTyped: () => SimulatorStatusToJSONTyped,
    SimulatorVersionDetailsFromJSON: () => SimulatorVersionDetailsFromJSON,
    SimulatorVersionDetailsFromJSONTyped: () => SimulatorVersionDetailsFromJSONTyped,
    SimulatorVersionDetailsToJSON: () => SimulatorVersionDetailsToJSON,
    SimulatorVersionDetailsToJSONTyped: () => SimulatorVersionDetailsToJSONTyped,
    SimulatorVersionsResponseFromJSON: () => SimulatorVersionsResponseFromJSON,
    SimulatorVersionsResponseFromJSONTyped: () => SimulatorVersionsResponseFromJSONTyped,
    SimulatorVersionsResponseToJSON: () => SimulatorVersionsResponseToJSON,
    SimulatorVersionsResponseToJSONTyped: () => SimulatorVersionsResponseToJSONTyped,
    TestcasesApi: () => TestcasesApi,
    TextApiResponse: () => TextApiResponse,
    UserApi: () => UserApi,
    VMManagementRequestFromJSON: () => VMManagementRequestFromJSON,
    VMManagementRequestFromJSONTyped: () => VMManagementRequestFromJSONTyped,
    VMManagementRequestToJSON: () => VMManagementRequestToJSON,
    VMManagementRequestToJSONTyped: () => VMManagementRequestToJSONTyped,
    VMManagementResponseFromJSON: () => VMManagementResponseFromJSON,
    VMManagementResponseFromJSONTyped: () => VMManagementResponseFromJSONTyped,
    VMManagementResponseToJSON: () => VMManagementResponseToJSON,
    VMManagementResponseToJSONTyped: () => VMManagementResponseToJSONTyped,
    ValidationErrorFromJSON: () => ValidationErrorFromJSON,
    ValidationErrorFromJSONTyped: () => ValidationErrorFromJSONTyped,
    ValidationErrorToJSON: () => ValidationErrorToJSON,
    ValidationErrorToJSONTyped: () => ValidationErrorToJSONTyped,
    VoidApiResponse: () => VoidApiResponse,
    WorkerReadyResponseFromJSON: () => WorkerReadyResponseFromJSON,
    WorkerReadyResponseFromJSONTyped: () => WorkerReadyResponseFromJSONTyped,
    WorkerReadyResponseToJSON: () => WorkerReadyResponseToJSON,
    WorkerReadyResponseToJSONTyped: () => WorkerReadyResponseToJSONTyped,
    canConsumeForm: () => canConsumeForm,
    exists: () => exists,
    instanceOfAuthentication: () => instanceOfAuthentication,
    instanceOfBaseScoringConfig: () => instanceOfBaseScoringConfig,
    instanceOfBaseStructuredRunLog: () => instanceOfBaseStructuredRunLog,
    instanceOfBatchLogRequest: () => instanceOfBatchLogRequest,
    instanceOfChromeCookie: () => instanceOfChromeCookie,
    instanceOfCreateSimulatorRequest: () => instanceOfCreateSimulatorRequest,
    instanceOfCreateSnapshotRequest: () => instanceOfCreateSnapshotRequest,
    instanceOfCreateSnapshotResponse: () => instanceOfCreateSnapshotResponse,
    instanceOfCreateVMRequest: () => instanceOfCreateVMRequest,
    instanceOfCreateVMResponse: () => instanceOfCreateVMResponse,
    instanceOfDbConfigResponse: () => instanceOfDbConfigResponse,
    instanceOfEvaluateRequest: () => instanceOfEvaluateRequest,
    instanceOfGetOperationEvents200Response: () => instanceOfGetOperationEvents200Response,
    instanceOfGetOperationEventsApiPublicBuildEventsCorrelationIdGet200Response: () => instanceOfGetOperationEventsApiPublicBuildEventsCorrelationIdGet200Response,
    instanceOfHTTPValidationError: () => instanceOfHTTPValidationError,
    instanceOfJobStatusResponse: () => instanceOfJobStatusResponse,
    instanceOfLocationInner: () => instanceOfLocationInner,
    instanceOfLog: () => instanceOfLog,
    instanceOfMakeEnvRequest2: () => instanceOfMakeEnvRequest2,
    instanceOfMakeEnvResponse: () => instanceOfMakeEnvResponse,
    instanceOfResetEnvRequest: () => instanceOfResetEnvRequest,
    instanceOfResetEnvTask: () => instanceOfResetEnvTask,
    instanceOfScoreRequest: () => instanceOfScoreRequest,
    instanceOfSetupRootPasswordRequest: () => instanceOfSetupRootPasswordRequest,
    instanceOfSetupSandboxRequest: () => instanceOfSetupSandboxRequest,
    instanceOfSetupSandboxResponse: () => instanceOfSetupSandboxResponse,
    instanceOfSimConfigCompute: () => instanceOfSimConfigCompute,
    instanceOfSimConfigDataset: () => instanceOfSimConfigDataset,
    instanceOfSimConfigListener: () => instanceOfSimConfigListener,
    instanceOfSimConfigMetadata: () => instanceOfSimConfigMetadata,
    instanceOfSimConfigService: () => instanceOfSimConfigService,
    instanceOfSimStatusHistory: () => instanceOfSimStatusHistory,
    instanceOfSimulatorConfig: () => instanceOfSimulatorConfig,
    instanceOfSimulatorListItem: () => instanceOfSimulatorListItem,
    instanceOfSimulatorStatus: () => instanceOfSimulatorStatus,
    instanceOfSimulatorVersionDetails: () => instanceOfSimulatorVersionDetails,
    instanceOfSimulatorVersionsResponse: () => instanceOfSimulatorVersionsResponse,
    instanceOfVMManagementRequest: () => instanceOfVMManagementRequest,
    instanceOfVMManagementResponse: () => instanceOfVMManagementResponse,
    instanceOfValidationError: () => instanceOfValidationError,
    instanceOfWorkerReadyResponse: () => instanceOfWorkerReadyResponse,
    mapValues: () => mapValues,
    querystring: () => querystring
  });

  // ../../sdk/typescript-sdk/src/runtime.ts
  var BASE_PATH = "http://localhost".replace(/\/+$/, "");
  var Configuration = class {
    constructor(configuration = {}) {
      this.configuration = configuration;
    }
    set config(configuration) {
      this.configuration = configuration;
    }
    get basePath() {
      return this.configuration.basePath != null ? this.configuration.basePath : BASE_PATH;
    }
    get fetchApi() {
      return this.configuration.fetchApi;
    }
    get middleware() {
      return this.configuration.middleware || [];
    }
    get queryParamsStringify() {
      return this.configuration.queryParamsStringify || querystring;
    }
    get username() {
      return this.configuration.username;
    }
    get password() {
      return this.configuration.password;
    }
    get apiKey() {
      const apiKey = this.configuration.apiKey;
      if (apiKey) {
        return typeof apiKey === "function" ? apiKey : () => apiKey;
      }
      return void 0;
    }
    get accessToken() {
      const accessToken = this.configuration.accessToken;
      if (accessToken) {
        return typeof accessToken === "function" ? accessToken : async () => accessToken;
      }
      return void 0;
    }
    get headers() {
      return this.configuration.headers;
    }
    get credentials() {
      return this.configuration.credentials;
    }
  };
  var DefaultConfig = new Configuration();
  var _BaseAPI = class _BaseAPI {
    constructor(configuration = DefaultConfig) {
      this.configuration = configuration;
      this.fetchApi = async (url, init) => {
        let fetchParams = { url, init };
        for (const middleware of this.middleware) {
          if (middleware.pre) {
            fetchParams = await middleware.pre({
              fetch: this.fetchApi,
              ...fetchParams
            }) || fetchParams;
          }
        }
        let response = void 0;
        try {
          response = await (this.configuration.fetchApi || fetch)(fetchParams.url, fetchParams.init);
        } catch (e) {
          for (const middleware of this.middleware) {
            if (middleware.onError) {
              response = await middleware.onError({
                fetch: this.fetchApi,
                url: fetchParams.url,
                init: fetchParams.init,
                error: e,
                response: response ? response.clone() : void 0
              }) || response;
            }
          }
          if (response === void 0) {
            if (e instanceof Error) {
              throw new FetchError(e, "The request failed and the interceptors did not return an alternative response");
            } else {
              throw e;
            }
          }
        }
        for (const middleware of this.middleware) {
          if (middleware.post) {
            response = await middleware.post({
              fetch: this.fetchApi,
              url: fetchParams.url,
              init: fetchParams.init,
              response: response.clone()
            }) || response;
          }
        }
        return response;
      };
      this.middleware = configuration.middleware;
    }
    withMiddleware(...middlewares) {
      const next = this.clone();
      next.middleware = next.middleware.concat(...middlewares);
      return next;
    }
    withPreMiddleware(...preMiddlewares) {
      const middlewares = preMiddlewares.map((pre) => ({ pre }));
      return this.withMiddleware(...middlewares);
    }
    withPostMiddleware(...postMiddlewares) {
      const middlewares = postMiddlewares.map((post) => ({ post }));
      return this.withMiddleware(...middlewares);
    }
    /**
     * Check if the given MIME is a JSON MIME.
     * JSON MIME examples:
     *   application/json
     *   application/json; charset=UTF8
     *   APPLICATION/JSON
     *   application/vnd.company+json
     * @param mime - MIME (Multipurpose Internet Mail Extensions)
     * @return True if the given MIME is JSON, false otherwise.
     */
    isJsonMime(mime) {
      if (!mime) {
        return false;
      }
      return _BaseAPI.jsonRegex.test(mime);
    }
    async request(context, initOverrides) {
      const { url, init } = await this.createFetchParams(context, initOverrides);
      const response = await this.fetchApi(url, init);
      if (response && (response.status >= 200 && response.status < 300)) {
        return response;
      }
      throw new ResponseError(response, "Response returned an error code");
    }
    async createFetchParams(context, initOverrides) {
      let url = this.configuration.basePath + context.path;
      if (context.query !== void 0 && Object.keys(context.query).length !== 0) {
        url += "?" + this.configuration.queryParamsStringify(context.query);
      }
      const headers = Object.assign({}, this.configuration.headers, context.headers);
      Object.keys(headers).forEach((key) => headers[key] === void 0 ? delete headers[key] : {});
      const initOverrideFn = typeof initOverrides === "function" ? initOverrides : async () => initOverrides;
      const initParams = {
        method: context.method,
        headers,
        body: context.body,
        credentials: this.configuration.credentials
      };
      const overriddenInit = {
        ...initParams,
        ...await initOverrideFn({
          init: initParams,
          context
        })
      };
      let body;
      if (isFormData(overriddenInit.body) || overriddenInit.body instanceof URLSearchParams || isBlob(overriddenInit.body)) {
        body = overriddenInit.body;
      } else if (this.isJsonMime(headers["Content-Type"])) {
        body = JSON.stringify(overriddenInit.body);
      } else {
        body = overriddenInit.body;
      }
      const init = {
        ...overriddenInit,
        body
      };
      return { url, init };
    }
    /**
     * Create a shallow clone of `this` by constructing a new instance
     * and then shallow cloning data members.
     */
    clone() {
      const constructor = this.constructor;
      const next = new constructor(this.configuration);
      next.middleware = this.middleware.slice();
      return next;
    }
  };
  _BaseAPI.jsonRegex = new RegExp("^(:?application/json|[^;/ 	]+/[^;/ 	]+[+]json)[ 	]*(:?;.*)?$", "i");
  var BaseAPI = _BaseAPI;
  function isBlob(value) {
    return typeof Blob !== "undefined" && value instanceof Blob;
  }
  function isFormData(value) {
    return typeof FormData !== "undefined" && value instanceof FormData;
  }
  var ResponseError = class extends Error {
    constructor(response, msg) {
      super(msg);
      this.response = response;
      this.name = "ResponseError";
    }
  };
  var FetchError = class extends Error {
    constructor(cause, msg) {
      super(msg);
      this.cause = cause;
      this.name = "FetchError";
    }
  };
  var RequiredError = class extends Error {
    constructor(field, msg) {
      super(msg);
      this.field = field;
      this.name = "RequiredError";
    }
  };
  var COLLECTION_FORMATS = {
    csv: ",",
    ssv: " ",
    tsv: "	",
    pipes: "|"
  };
  function querystring(params, prefix = "") {
    return Object.keys(params).map((key) => querystringSingleKey(key, params[key], prefix)).filter((part) => part.length > 0).join("&");
  }
  function querystringSingleKey(key, value, keyPrefix = "") {
    const fullKey = keyPrefix + (keyPrefix.length ? `[${key}]` : key);
    if (value instanceof Array) {
      const multiValue = value.map((singleValue) => encodeURIComponent(String(singleValue))).join(`&${encodeURIComponent(fullKey)}=`);
      return `${encodeURIComponent(fullKey)}=${multiValue}`;
    }
    if (value instanceof Set) {
      const valueAsArray = Array.from(value);
      return querystringSingleKey(key, valueAsArray, keyPrefix);
    }
    if (value instanceof Date) {
      return `${encodeURIComponent(fullKey)}=${encodeURIComponent(value.toISOString())}`;
    }
    if (value instanceof Object) {
      return querystring(value, fullKey);
    }
    return `${encodeURIComponent(fullKey)}=${encodeURIComponent(String(value))}`;
  }
  function exists(json, key) {
    const value = json[key];
    return value !== null && value !== void 0;
  }
  function mapValues(data, fn) {
    const result = {};
    for (const key of Object.keys(data)) {
      result[key] = fn(data[key]);
    }
    return result;
  }
  function canConsumeForm(consumes) {
    for (const consume of consumes) {
      if ("multipart/form-data" === consume.contentType) {
        return true;
      }
    }
    return false;
  }
  var JSONApiResponse = class {
    constructor(raw, transformer = (jsonValue) => jsonValue) {
      this.raw = raw;
      this.transformer = transformer;
    }
    async value() {
      return this.transformer(await this.raw.json());
    }
  };
  var VoidApiResponse = class {
    constructor(raw) {
      this.raw = raw;
    }
    async value() {
      return void 0;
    }
  };
  var BlobApiResponse = class {
    constructor(raw) {
      this.raw = raw;
    }
    async value() {
      return await this.raw.blob();
    }
  };
  var TextApiResponse = class {
    constructor(raw) {
      this.raw = raw;
    }
    async value() {
      return await this.raw.text();
    }
  };

  // ../../sdk/typescript-sdk/src/models/Authentication.ts
  function instanceOfAuthentication(value) {
    if (!("user" in value) || value["user"] === void 0) return false;
    if (!("password" in value) || value["password"] === void 0) return false;
    return true;
  }
  function AuthenticationFromJSON(json) {
    return AuthenticationFromJSONTyped(json, false);
  }
  function AuthenticationFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "user": json["user"],
      "password": json["password"]
    };
  }
  function AuthenticationToJSON(json) {
    return AuthenticationToJSONTyped(json, false);
  }
  function AuthenticationToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "user": value["user"],
      "password": value["password"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/BaseScoringConfig.ts
  var BaseScoringConfigTypeEnum = {
    OfflineStep: "offline_step",
    OfflineExactActionMatch: "offline_exact_action_match",
    OfflineExactStateMatch: "offline_exact_state_match",
    OfflineExactOutputMatch: "offline_exact_output_match",
    PageActionSequence: "page_action_sequence",
    HumanInTheLoop: "human_in_the_loop",
    Api: "api",
    Criteria: "criteria",
    RealEvalsStateCheck: "real_evals_state_check",
    RealEvalsResponseCheck: "real_evals_response_check",
    Composite: "composite",
    Custom: "custom",
    StateMutationMatch: "state_mutation_match",
    SystemScoring: "system_scoring",
    JsonSchema: "json_schema"
  };
  function instanceOfBaseScoringConfig(value) {
    if (!("type" in value) || value["type"] === void 0) return false;
    return true;
  }
  function BaseScoringConfigFromJSON(json) {
    return BaseScoringConfigFromJSONTyped(json, false);
  }
  function BaseScoringConfigFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "type": json["type"]
    };
  }
  function BaseScoringConfigToJSON(json) {
    return BaseScoringConfigToJSONTyped(json, false);
  }
  function BaseScoringConfigToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "type": value["type"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/BaseStructuredRunLog.ts
  var BaseStructuredRunLogSourceEnum = {
    System: "system",
    Agent: "agent",
    Simulator: "simulator"
  };
  var BaseStructuredRunLogTypeEnum = {
    Info: "info",
    Warning: "warning",
    Error: "error",
    Answer: "answer",
    Action: "action",
    StateMutation: "state_mutation",
    OodRequest: "ood_request",
    ScreenRecordingStarted: "screen_recording_started"
  };
  function instanceOfBaseStructuredRunLog(value) {
    return true;
  }
  function BaseStructuredRunLogFromJSON(json) {
    return BaseStructuredRunLogFromJSONTyped(json, false);
  }
  function BaseStructuredRunLogFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "source": json["source"] == null ? void 0 : json["source"],
      "type": json["type"] == null ? void 0 : json["type"],
      "timestamp": json["timestamp"] == null ? void 0 : json["timestamp"]
    };
  }
  function BaseStructuredRunLogToJSON(json) {
    return BaseStructuredRunLogToJSONTyped(json, false);
  }
  function BaseStructuredRunLogToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "source": value["source"],
      "type": value["type"],
      "timestamp": value["timestamp"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/BatchLogRequest.ts
  function instanceOfBatchLogRequest(value) {
    if (!("source" in value) || value["source"] === void 0) return false;
    if (!("type" in value) || value["type"] === void 0) return false;
    if (!("timestamp" in value) || value["timestamp"] === void 0) return false;
    if (!("sessionId" in value) || value["sessionId"] === void 0) return false;
    if (!("mutations" in value) || value["mutations"] === void 0) return false;
    if (!("count" in value) || value["count"] === void 0) return false;
    return true;
  }
  function BatchLogRequestFromJSON(json) {
    return BatchLogRequestFromJSONTyped(json, false);
  }
  function BatchLogRequestFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "source": json["source"],
      "type": json["type"],
      "timestamp": json["timestamp"],
      "sessionId": json["session_id"],
      "mutations": json["mutations"].map(BaseStructuredRunLogFromJSON),
      "count": json["count"]
    };
  }
  function BatchLogRequestToJSON(json) {
    return BatchLogRequestToJSONTyped(json, false);
  }
  function BatchLogRequestToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "source": value["source"],
      "type": value["type"],
      "timestamp": value["timestamp"],
      "session_id": value["sessionId"],
      "mutations": value["mutations"].map(BaseStructuredRunLogToJSON),
      "count": value["count"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/ChromeCookie.ts
  function instanceOfChromeCookie(value) {
    if (!("name" in value) || value["name"] === void 0) return false;
    if (!("value" in value) || value["value"] === void 0) return false;
    if (!("domain" in value) || value["domain"] === void 0) return false;
    if (!("path" in value) || value["path"] === void 0) return false;
    if (!("expires" in value) || value["expires"] === void 0) return false;
    if (!("httpOnly" in value) || value["httpOnly"] === void 0) return false;
    if (!("secure" in value) || value["secure"] === void 0) return false;
    return true;
  }
  function ChromeCookieFromJSON(json) {
    return ChromeCookieFromJSONTyped(json, false);
  }
  function ChromeCookieFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "name": json["name"],
      "value": json["value"],
      "domain": json["domain"],
      "path": json["path"],
      "expires": json["expires"],
      "httpOnly": json["httpOnly"],
      "secure": json["secure"]
    };
  }
  function ChromeCookieToJSON(json) {
    return ChromeCookieToJSONTyped(json, false);
  }
  function ChromeCookieToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "name": value["name"],
      "value": value["value"],
      "domain": value["domain"],
      "path": value["path"],
      "expires": value["expires"],
      "httpOnly": value["httpOnly"],
      "secure": value["secure"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/SimStatusHistory.ts
  function instanceOfSimStatusHistory(value) {
    if (!("timestampIso" in value) || value["timestampIso"] === void 0) return false;
    if (!("oldStatus" in value) || value["oldStatus"] === void 0) return false;
    if (!("newStatus" in value) || value["newStatus"] === void 0) return false;
    return true;
  }
  function SimStatusHistoryFromJSON(json) {
    return SimStatusHistoryFromJSONTyped(json, false);
  }
  function SimStatusHistoryFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "timestampIso": json["timestamp_iso"],
      "oldStatus": json["old_status"],
      "newStatus": json["new_status"],
      "userId": json["user_id"] == null ? void 0 : json["user_id"]
    };
  }
  function SimStatusHistoryToJSON(json) {
    return SimStatusHistoryToJSONTyped(json, false);
  }
  function SimStatusHistoryToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "timestamp_iso": value["timestampIso"],
      "old_status": value["oldStatus"],
      "new_status": value["newStatus"],
      "user_id": value["userId"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/SimulatorConfig.ts
  var SimulatorConfigTypeEnum = {
    Proxy: "proxy",
    DockerApp: "docker_app"
  };
  var SimulatorConfigStatusEnum = {
    Requested: "requested",
    InProgress: "in_progress",
    EnvironmentInProgress: "environment_in_progress",
    EnvironmentReady: "environment_ready",
    DataInProgress: "data_in_progress",
    DataReady: "data_ready",
    TasksInProgress: "tasks_in_progress",
    NotStarted: "not_started",
    EnvInProgress: "env_in_progress",
    EnvReviewRequested: "env_review_requested",
    EnvApproved: "env_approved",
    DataReviewRequested: "data_review_requested",
    Ready: "ready",
    ReadyDisabledTesting: "ready-disabled-testing",
    OutOfService: "out_of_service"
  };
  function instanceOfSimulatorConfig(value) {
    if (!("type" in value) || value["type"] === void 0) return false;
    return true;
  }
  function SimulatorConfigFromJSON(json) {
    return SimulatorConfigFromJSONTyped(json, false);
  }
  function SimulatorConfigFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "type": json["type"],
      "cookies": json["cookies"] == null ? void 0 : json["cookies"].map(ChromeCookieFromJSON),
      "authentication": json["authentication"] == null ? void 0 : AuthenticationFromJSON(json["authentication"]),
      "defaultStartPath": json["default_start_path"] == null ? void 0 : json["default_start_path"],
      "status": json["status"] == null ? void 0 : json["status"],
      "envAssignees": json["env_assignees"] == null ? void 0 : json["env_assignees"],
      "envReviewAssignees": json["env_review_assignees"] == null ? void 0 : json["env_review_assignees"],
      "dataAssignees": json["data_assignees"] == null ? void 0 : json["data_assignees"],
      "dataReviewAssignees": json["data_review_assignees"] == null ? void 0 : json["data_review_assignees"],
      "statusHistory": json["status_history"] == null ? void 0 : json["status_history"].map(SimStatusHistoryFromJSON),
      "assignedUserId": json["assigned_user_id"] == null ? void 0 : json["assigned_user_id"],
      "notes": json["notes"] == null ? void 0 : json["notes"]
    };
  }
  function SimulatorConfigToJSON(json) {
    return SimulatorConfigToJSONTyped(json, false);
  }
  function SimulatorConfigToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "type": value["type"],
      "cookies": value["cookies"] == null ? void 0 : value["cookies"].map(ChromeCookieToJSON),
      "authentication": AuthenticationToJSON(value["authentication"]),
      "default_start_path": value["defaultStartPath"],
      "status": value["status"],
      "env_assignees": value["envAssignees"],
      "env_review_assignees": value["envReviewAssignees"],
      "data_assignees": value["dataAssignees"],
      "data_review_assignees": value["dataReviewAssignees"],
      "status_history": value["statusHistory"] == null ? void 0 : value["statusHistory"].map(SimStatusHistoryToJSON),
      "assigned_user_id": value["assignedUserId"],
      "notes": value["notes"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/CreateSimulatorRequest.ts
  function instanceOfCreateSimulatorRequest(value) {
    if (!("name" in value) || value["name"] === void 0) return false;
    if (!("config" in value) || value["config"] === void 0) return false;
    if (!("simType" in value) || value["simType"] === void 0) return false;
    return true;
  }
  function CreateSimulatorRequestFromJSON(json) {
    return CreateSimulatorRequestFromJSONTyped(json, false);
  }
  function CreateSimulatorRequestFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "name": json["name"],
      "url": json["url"] == null ? void 0 : json["url"],
      "description": json["description"] == null ? void 0 : json["description"],
      "imgUrl": json["imgUrl"] == null ? void 0 : json["imgUrl"],
      "config": SimulatorConfigFromJSON(json["config"]),
      "ancestors": json["ancestors"] == null ? void 0 : json["ancestors"],
      "enabled": json["enabled"] == null ? void 0 : json["enabled"],
      "simType": json["simType"],
      "jobName": json["jobName"] == null ? void 0 : json["jobName"],
      "internalAppPort": json["internalAppPort"] == null ? void 0 : json["internalAppPort"],
      "supportedProviders": json["supportedProviders"] == null ? void 0 : json["supportedProviders"]
    };
  }
  function CreateSimulatorRequestToJSON(json) {
    return CreateSimulatorRequestToJSONTyped(json, false);
  }
  function CreateSimulatorRequestToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "name": value["name"],
      "url": value["url"],
      "description": value["description"],
      "imgUrl": value["imgUrl"],
      "config": SimulatorConfigToJSON(value["config"]),
      "ancestors": value["ancestors"],
      "enabled": value["enabled"],
      "simType": value["simType"],
      "jobName": value["jobName"],
      "internalAppPort": value["internalAppPort"],
      "supportedProviders": value["supportedProviders"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/CreateSnapshotRequest.ts
  function instanceOfCreateSnapshotRequest(value) {
    return true;
  }
  function CreateSnapshotRequestFromJSON(json) {
    return CreateSnapshotRequestFromJSONTyped(json, false);
  }
  function CreateSnapshotRequestFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "service": json["service"] == null ? void 0 : json["service"],
      "gitHash": json["git_hash"] == null ? void 0 : json["git_hash"],
      "dataset": json["dataset"] == null ? void 0 : json["dataset"],
      "notes": json["notes"] == null ? void 0 : json["notes"],
      "flows": json["flows"] == null ? void 0 : json["flows"],
      "platoConfig": json["plato_config"] == null ? void 0 : json["plato_config"],
      "internalAppPort": json["internal_app_port"] == null ? void 0 : json["internal_app_port"],
      "messagingPort": json["messaging_port"] == null ? void 0 : json["messaging_port"]
    };
  }
  function CreateSnapshotRequestToJSON(json) {
    return CreateSnapshotRequestToJSONTyped(json, false);
  }
  function CreateSnapshotRequestToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "service": value["service"],
      "git_hash": value["gitHash"],
      "dataset": value["dataset"],
      "notes": value["notes"],
      "flows": value["flows"],
      "plato_config": value["platoConfig"],
      "internal_app_port": value["internalAppPort"],
      "messaging_port": value["messagingPort"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/CreateSnapshotResponse.ts
  function instanceOfCreateSnapshotResponse(value) {
    if (!("artifactId" in value) || value["artifactId"] === void 0) return false;
    if (!("status" in value) || value["status"] === void 0) return false;
    if (!("timestamp" in value) || value["timestamp"] === void 0) return false;
    if (!("correlationId" in value) || value["correlationId"] === void 0) return false;
    if (!("s3Uri" in value) || value["s3Uri"] === void 0) return false;
    return true;
  }
  function CreateSnapshotResponseFromJSON(json) {
    return CreateSnapshotResponseFromJSONTyped(json, false);
  }
  function CreateSnapshotResponseFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "artifactId": json["artifact_id"],
      "status": json["status"],
      "timestamp": json["timestamp"],
      "correlationId": json["correlation_id"],
      "s3Uri": json["s3_uri"]
    };
  }
  function CreateSnapshotResponseToJSON(json) {
    return CreateSnapshotResponseToJSONTyped(json, false);
  }
  function CreateSnapshotResponseToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "artifact_id": value["artifactId"],
      "status": value["status"],
      "timestamp": value["timestamp"],
      "correlation_id": value["correlationId"],
      "s3_uri": value["s3Uri"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/SimConfigCompute.ts
  function instanceOfSimConfigCompute(value) {
    return true;
  }
  function SimConfigComputeFromJSON(json) {
    return SimConfigComputeFromJSONTyped(json, false);
  }
  function SimConfigComputeFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "cpus": json["cpus"] == null ? void 0 : json["cpus"],
      "memory": json["memory"] == null ? void 0 : json["memory"],
      "disk": json["disk"] == null ? void 0 : json["disk"],
      "appPort": json["app_port"] == null ? void 0 : json["app_port"],
      "platoMessagingPort": json["plato_messaging_port"] == null ? void 0 : json["plato_messaging_port"]
    };
  }
  function SimConfigComputeToJSON(json) {
    return SimConfigComputeToJSONTyped(json, false);
  }
  function SimConfigComputeToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "cpus": value["cpus"],
      "memory": value["memory"],
      "disk": value["disk"],
      "app_port": value["appPort"],
      "plato_messaging_port": value["platoMessagingPort"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/SimConfigService.ts
  var SimConfigServiceTypeEnum = {
    DockerCompose: "docker-compose",
    Docker: "docker"
  };
  function instanceOfSimConfigService(value) {
    if (!("type" in value) || value["type"] === void 0) return false;
    return true;
  }
  function SimConfigServiceFromJSON(json) {
    return SimConfigServiceFromJSONTyped(json, false);
  }
  function SimConfigServiceFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "type": json["type"]
    };
  }
  function SimConfigServiceToJSON(json) {
    return SimConfigServiceToJSONTyped(json, false);
  }
  function SimConfigServiceToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "type": value["type"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/SimConfigMetadata.ts
  function instanceOfSimConfigMetadata(value) {
    return true;
  }
  function SimConfigMetadataFromJSON(json) {
    return SimConfigMetadataFromJSONTyped(json, false);
  }
  function SimConfigMetadataFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "favicon": json["favicon"] == null ? void 0 : json["favicon"],
      "name": json["name"] == null ? void 0 : json["name"],
      "description": json["description"] == null ? void 0 : json["description"],
      "sourceCodeUrl": json["source_code_url"] == null ? void 0 : json["source_code_url"],
      "startUrl": json["start_url"] == null ? void 0 : json["start_url"],
      "license": json["license"] == null ? void 0 : json["license"],
      "variables": json["variables"] == null ? void 0 : json["variables"],
      "flowsPath": json["flows_path"] == null ? void 0 : json["flows_path"]
    };
  }
  function SimConfigMetadataToJSON(json) {
    return SimConfigMetadataToJSONTyped(json, false);
  }
  function SimConfigMetadataToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "favicon": value["favicon"],
      "name": value["name"],
      "description": value["description"],
      "source_code_url": value["sourceCodeUrl"],
      "start_url": value["startUrl"],
      "license": value["license"],
      "variables": value["variables"],
      "flows_path": value["flowsPath"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/SimConfigListener.ts
  var SimConfigListenerTypeEnum = {
    Db: "db",
    Proxy: "proxy",
    File: "file"
  };
  function instanceOfSimConfigListener(value) {
    if (!("type" in value) || value["type"] === void 0) return false;
    return true;
  }
  function SimConfigListenerFromJSON(json) {
    return SimConfigListenerFromJSONTyped(json, false);
  }
  function SimConfigListenerFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "type": json["type"]
    };
  }
  function SimConfigListenerToJSON(json) {
    return SimConfigListenerToJSONTyped(json, false);
  }
  function SimConfigListenerToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "type": value["type"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/SimConfigDataset.ts
  function instanceOfSimConfigDataset(value) {
    if (!("compute" in value) || value["compute"] === void 0) return false;
    if (!("metadata" in value) || value["metadata"] === void 0) return false;
    if (!("services" in value) || value["services"] === void 0) return false;
    if (!("listeners" in value) || value["listeners"] === void 0) return false;
    return true;
  }
  function SimConfigDatasetFromJSON(json) {
    return SimConfigDatasetFromJSONTyped(json, false);
  }
  function SimConfigDatasetFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "compute": SimConfigComputeFromJSON(json["compute"]),
      "metadata": SimConfigMetadataFromJSON(json["metadata"]),
      "services": json["services"] == null ? null : mapValues(json["services"], SimConfigServiceFromJSON),
      "listeners": json["listeners"] == null ? null : mapValues(json["listeners"], SimConfigListenerFromJSON)
    };
  }
  function SimConfigDatasetToJSON(json) {
    return SimConfigDatasetToJSONTyped(json, false);
  }
  function SimConfigDatasetToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "compute": SimConfigComputeToJSON(value["compute"]),
      "metadata": SimConfigMetadataToJSON(value["metadata"]),
      "services": value["services"] == null ? null : mapValues(value["services"], SimConfigServiceToJSON),
      "listeners": value["listeners"] == null ? null : mapValues(value["listeners"], SimConfigListenerToJSON)
    };
  }

  // ../../sdk/typescript-sdk/src/models/CreateVMRequest.ts
  function instanceOfCreateVMRequest(value) {
    if (!("dataset" in value) || value["dataset"] === void 0) return false;
    if (!("platoDatasetConfig" in value) || value["platoDatasetConfig"] === void 0) return false;
    return true;
  }
  function CreateVMRequestFromJSON(json) {
    return CreateVMRequestFromJSONTyped(json, false);
  }
  function CreateVMRequestFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "service": json["service"] == null ? void 0 : json["service"],
      "dataset": json["dataset"],
      "platoDatasetConfig": SimConfigDatasetFromJSON(json["plato_dataset_config"]),
      "requestTimeout": json["request_timeout"] == null ? void 0 : json["request_timeout"],
      "artifactId": json["artifact_id"] == null ? void 0 : json["artifact_id"],
      "alias": json["alias"] == null ? void 0 : json["alias"],
      "sandboxTimeout": json["sandbox_timeout"] == null ? void 0 : json["sandbox_timeout"]
    };
  }
  function CreateVMRequestToJSON(json) {
    return CreateVMRequestToJSONTyped(json, false);
  }
  function CreateVMRequestToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "service": value["service"],
      "dataset": value["dataset"],
      "plato_dataset_config": SimConfigDatasetToJSON(value["platoDatasetConfig"]),
      "request_timeout": value["requestTimeout"],
      "artifact_id": value["artifactId"],
      "alias": value["alias"],
      "sandbox_timeout": value["sandboxTimeout"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/CreateVMResponse.ts
  function instanceOfCreateVMResponse(value) {
    if (!("status" in value) || value["status"] === void 0) return false;
    if (!("correlationId" in value) || value["correlationId"] === void 0) return false;
    if (!("url" in value) || value["url"] === void 0) return false;
    if (!("jobPublicId" in value) || value["jobPublicId"] === void 0) return false;
    if (!("jobGroupId" in value) || value["jobGroupId"] === void 0) return false;
    return true;
  }
  function CreateVMResponseFromJSON(json) {
    return CreateVMResponseFromJSONTyped(json, false);
  }
  function CreateVMResponseFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "status": json["status"],
      "timestamp": json["timestamp"] == null ? void 0 : json["timestamp"],
      "correlationId": json["correlation_id"],
      "url": json["url"],
      "jobPublicId": json["job_public_id"],
      "jobGroupId": json["job_group_id"]
    };
  }
  function CreateVMResponseToJSON(json) {
    return CreateVMResponseToJSONTyped(json, false);
  }
  function CreateVMResponseToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "status": value["status"],
      "timestamp": value["timestamp"],
      "correlation_id": value["correlationId"],
      "url": value["url"],
      "job_public_id": value["jobPublicId"],
      "job_group_id": value["jobGroupId"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/DbConfigResponse.ts
  function instanceOfDbConfigResponse(value) {
    if (!("dbType" in value) || value["dbType"] === void 0) return false;
    if (!("dbPort" in value) || value["dbPort"] === void 0) return false;
    if (!("dbUser" in value) || value["dbUser"] === void 0) return false;
    if (!("dbPassword" in value) || value["dbPassword"] === void 0) return false;
    if (!("dbDatabase" in value) || value["dbDatabase"] === void 0) return false;
    return true;
  }
  function DbConfigResponseFromJSON(json) {
    return DbConfigResponseFromJSONTyped(json, false);
  }
  function DbConfigResponseFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "dbType": json["db_type"],
      "dbPort": json["db_port"],
      "dbUser": json["db_user"],
      "dbPassword": json["db_password"],
      "dbDatabase": json["db_database"]
    };
  }
  function DbConfigResponseToJSON(json) {
    return DbConfigResponseToJSONTyped(json, false);
  }
  function DbConfigResponseToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "db_type": value["dbType"],
      "db_port": value["dbPort"],
      "db_user": value["dbUser"],
      "db_password": value["dbPassword"],
      "db_database": value["dbDatabase"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/EvaluateRequest.ts
  function instanceOfEvaluateRequest(value) {
    return true;
  }
  function EvaluateRequestFromJSON(json) {
    return EvaluateRequestFromJSONTyped(json, false);
  }
  function EvaluateRequestFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "value": json["value"] == null ? void 0 : json["value"]
    };
  }
  function EvaluateRequestToJSON(json) {
    return EvaluateRequestToJSONTyped(json, false);
  }
  function EvaluateRequestToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "value": value["value"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/GetOperationEvents200Response.ts
  var GetOperationEvents200ResponseTypeEnum = {
    Connected: "connected",
    Progress: "progress",
    Complete: "complete",
    Error: "error"
  };
  function instanceOfGetOperationEvents200Response(value) {
    if (!("type" in value) || value["type"] === void 0) return false;
    return true;
  }
  function GetOperationEvents200ResponseFromJSON(json) {
    return GetOperationEvents200ResponseFromJSONTyped(json, false);
  }
  function GetOperationEvents200ResponseFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "type": json["type"],
      "success": json["success"] == null ? void 0 : json["success"],
      "message": json["message"] == null ? void 0 : json["message"],
      "error": json["error"] == null ? void 0 : json["error"]
    };
  }
  function GetOperationEvents200ResponseToJSON(json) {
    return GetOperationEvents200ResponseToJSONTyped(json, false);
  }
  function GetOperationEvents200ResponseToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "type": value["type"],
      "success": value["success"],
      "message": value["message"],
      "error": value["error"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/LocationInner.ts
  function instanceOfLocationInner(value) {
    return true;
  }
  function LocationInnerFromJSON(json) {
    return LocationInnerFromJSONTyped(json, false);
  }
  function LocationInnerFromJSONTyped(json, ignoreDiscriminator) {
    return json;
  }
  function LocationInnerToJSON(json) {
    return LocationInnerToJSONTyped(json, false);
  }
  function LocationInnerToJSONTyped(value, ignoreDiscriminator = false) {
    return value;
  }

  // ../../sdk/typescript-sdk/src/models/ValidationError.ts
  function instanceOfValidationError(value) {
    if (!("loc" in value) || value["loc"] === void 0) return false;
    if (!("msg" in value) || value["msg"] === void 0) return false;
    if (!("type" in value) || value["type"] === void 0) return false;
    return true;
  }
  function ValidationErrorFromJSON(json) {
    return ValidationErrorFromJSONTyped(json, false);
  }
  function ValidationErrorFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "loc": json["loc"].map(LocationInnerFromJSON),
      "msg": json["msg"],
      "type": json["type"]
    };
  }
  function ValidationErrorToJSON(json) {
    return ValidationErrorToJSONTyped(json, false);
  }
  function ValidationErrorToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "loc": value["loc"].map(LocationInnerToJSON),
      "msg": value["msg"],
      "type": value["type"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/HTTPValidationError.ts
  function instanceOfHTTPValidationError(value) {
    return true;
  }
  function HTTPValidationErrorFromJSON(json) {
    return HTTPValidationErrorFromJSONTyped(json, false);
  }
  function HTTPValidationErrorFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "detail": json["detail"] == null ? void 0 : json["detail"].map(ValidationErrorFromJSON)
    };
  }
  function HTTPValidationErrorToJSON(json) {
    return HTTPValidationErrorToJSONTyped(json, false);
  }
  function HTTPValidationErrorToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "detail": value["detail"] == null ? void 0 : value["detail"].map(ValidationErrorToJSON)
    };
  }

  // ../../sdk/typescript-sdk/src/models/JobStatusResponse.ts
  function instanceOfJobStatusResponse(value) {
    if (!("status" in value) || value["status"] === void 0) return false;
    if (!("statusReason" in value) || value["statusReason"] === void 0) return false;
    if (!("createdAt" in value) || value["createdAt"] === void 0) return false;
    if (!("updatedAt" in value) || value["updatedAt"] === void 0) return false;
    return true;
  }
  function JobStatusResponseFromJSON(json) {
    return JobStatusResponseFromJSONTyped(json, false);
  }
  function JobStatusResponseFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "status": json["status"],
      "statusReason": json["status_reason"],
      "createdAt": new Date(json["created_at"]),
      "updatedAt": new Date(json["updated_at"])
    };
  }
  function JobStatusResponseToJSON(json) {
    return JobStatusResponseToJSONTyped(json, false);
  }
  function JobStatusResponseToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "status": value["status"],
      "status_reason": value["statusReason"],
      "created_at": value["createdAt"].toISOString(),
      "updated_at": value["updatedAt"].toISOString()
    };
  }

  // ../../sdk/typescript-sdk/src/models/Log.ts
  function instanceOfLog(value) {
    if (!("source" in value) || value["source"] === void 0) return false;
    if (!("type" in value) || value["type"] === void 0) return false;
    if (!("timestamp" in value) || value["timestamp"] === void 0) return false;
    if (!("sessionId" in value) || value["sessionId"] === void 0) return false;
    if (!("mutations" in value) || value["mutations"] === void 0) return false;
    if (!("count" in value) || value["count"] === void 0) return false;
    return true;
  }
  function LogFromJSON(json) {
    return LogFromJSONTyped(json, false);
  }
  function LogFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "source": json["source"],
      "type": json["type"],
      "timestamp": json["timestamp"],
      "sessionId": json["session_id"],
      "mutations": json["mutations"].map(BaseStructuredRunLogFromJSON),
      "count": json["count"]
    };
  }
  function LogToJSON(json) {
    return LogToJSONTyped(json, false);
  }
  function LogToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "source": value["source"],
      "type": value["type"],
      "timestamp": value["timestamp"],
      "session_id": value["sessionId"],
      "mutations": value["mutations"].map(BaseStructuredRunLogToJSON),
      "count": value["count"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/MakeEnvRequest2.ts
  var MakeEnvRequest2InterfaceTypeEnum = {
    Browser: "browser",
    Computer: "computer",
    Noop: "noop"
  };
  function instanceOfMakeEnvRequest2(value) {
    if (!("interfaceType" in value) || value["interfaceType"] === void 0) return false;
    if (!("source" in value) || value["source"] === void 0) return false;
    if (!("envId" in value) || value["envId"] === void 0) return false;
    if (!("envConfig" in value) || value["envConfig"] === void 0) return false;
    return true;
  }
  function MakeEnvRequest2FromJSON(json) {
    return MakeEnvRequest2FromJSONTyped(json, false);
  }
  function MakeEnvRequest2FromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "interfaceType": json["interface_type"],
      "interfaceWidth": json["interface_width"] == null ? void 0 : json["interface_width"],
      "interfaceHeight": json["interface_height"] == null ? void 0 : json["interface_height"],
      "source": json["source"],
      "openPageOnStart": json["open_page_on_start"] == null ? void 0 : json["open_page_on_start"],
      "envId": json["env_id"],
      "envConfig": json["env_config"],
      "recordNetworkRequests": json["record_network_requests"] == null ? void 0 : json["record_network_requests"],
      "recordActions": json["record_actions"] == null ? void 0 : json["record_actions"],
      "loadChromeExtensions": json["load_chrome_extensions"] == null ? void 0 : json["load_chrome_extensions"],
      "keepalive": json["keepalive"] == null ? void 0 : json["keepalive"],
      "alias": json["alias"] == null ? void 0 : json["alias"],
      "fast": json["fast"] == null ? void 0 : json["fast"],
      "version": json["version"] == null ? void 0 : json["version"],
      "tag": json["tag"] == null ? void 0 : json["tag"],
      "dataset": json["dataset"] == null ? void 0 : json["dataset"],
      "artifactId": json["artifact_id"] == null ? void 0 : json["artifact_id"],
      "timeout": json["timeout"] == null ? void 0 : json["timeout"]
    };
  }
  function MakeEnvRequest2ToJSON(json) {
    return MakeEnvRequest2ToJSONTyped(json, false);
  }
  function MakeEnvRequest2ToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "interface_type": value["interfaceType"],
      "interface_width": value["interfaceWidth"],
      "interface_height": value["interfaceHeight"],
      "source": value["source"],
      "open_page_on_start": value["openPageOnStart"],
      "env_id": value["envId"],
      "env_config": value["envConfig"],
      "record_network_requests": value["recordNetworkRequests"],
      "record_actions": value["recordActions"],
      "load_chrome_extensions": value["loadChromeExtensions"],
      "keepalive": value["keepalive"],
      "alias": value["alias"],
      "fast": value["fast"],
      "version": value["version"],
      "tag": value["tag"],
      "dataset": value["dataset"],
      "artifact_id": value["artifactId"],
      "timeout": value["timeout"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/ResetEnvTask.ts
  function instanceOfResetEnvTask(value) {
    if (!("prompt" in value) || value["prompt"] === void 0) return false;
    if (!("name" in value) || value["name"] === void 0) return false;
    return true;
  }
  function ResetEnvTaskFromJSON(json) {
    return ResetEnvTaskFromJSONTyped(json, false);
  }
  function ResetEnvTaskFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "prompt": json["prompt"],
      "startUrl": json["start_url"] == null ? void 0 : json["start_url"],
      "name": json["name"],
      "datasetName": json["dataset_name"] == null ? void 0 : json["dataset_name"],
      "evalConfig": json["eval_config"] == null ? void 0 : BaseScoringConfigFromJSON(json["eval_config"])
    };
  }
  function ResetEnvTaskToJSON(json) {
    return ResetEnvTaskToJSONTyped(json, false);
  }
  function ResetEnvTaskToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "prompt": value["prompt"],
      "start_url": value["startUrl"],
      "name": value["name"],
      "dataset_name": value["datasetName"],
      "eval_config": BaseScoringConfigToJSON(value["evalConfig"])
    };
  }

  // ../../sdk/typescript-sdk/src/models/ResetEnvRequest.ts
  function instanceOfResetEnvRequest(value) {
    return true;
  }
  function ResetEnvRequestFromJSON(json) {
    return ResetEnvRequestFromJSONTyped(json, false);
  }
  function ResetEnvRequestFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "task": json["task"] == null ? void 0 : ResetEnvTaskFromJSON(json["task"]),
      "agentVersion": json["agent_version"] == null ? void 0 : json["agent_version"],
      "model": json["model"] == null ? void 0 : json["model"],
      "source": json["source"] == null ? void 0 : json["source"],
      "loadBrowserState": json["load_browser_state"] == null ? void 0 : json["load_browser_state"],
      "viewportWidth": json["viewport_width"] == null ? void 0 : json["viewport_width"],
      "viewportHeight": json["viewport_height"] == null ? void 0 : json["viewport_height"],
      "testCasePublicId": json["test_case_public_id"] == null ? void 0 : json["test_case_public_id"],
      "replayedFromSessionId": json["replayed_from_session_id"] == null ? void 0 : json["replayed_from_session_id"],
      "userId": json["user_id"] == null ? void 0 : json["user_id"]
    };
  }
  function ResetEnvRequestToJSON(json) {
    return ResetEnvRequestToJSONTyped(json, false);
  }
  function ResetEnvRequestToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "task": ResetEnvTaskToJSON(value["task"]),
      "agent_version": value["agentVersion"],
      "model": value["model"],
      "source": value["source"],
      "load_browser_state": value["loadBrowserState"],
      "viewport_width": value["viewportWidth"],
      "viewport_height": value["viewportHeight"],
      "test_case_public_id": value["testCasePublicId"],
      "replayed_from_session_id": value["replayedFromSessionId"],
      "user_id": value["userId"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/ScoreRequest.ts
  function instanceOfScoreRequest(value) {
    if (!("success" in value) || value["success"] === void 0) return false;
    return true;
  }
  function ScoreRequestFromJSON(json) {
    return ScoreRequestFromJSONTyped(json, false);
  }
  function ScoreRequestFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "success": json["success"],
      "reason": json["reason"] == null ? void 0 : json["reason"],
      "agentVersion": json["agent_version"] == null ? void 0 : json["agent_version"],
      "mutations": json["mutations"] == null ? void 0 : json["mutations"]
    };
  }
  function ScoreRequestToJSON(json) {
    return ScoreRequestToJSONTyped(json, false);
  }
  function ScoreRequestToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "success": value["success"],
      "reason": value["reason"],
      "agent_version": value["agentVersion"],
      "mutations": value["mutations"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/SetupRootPasswordRequest.ts
  function instanceOfSetupRootPasswordRequest(value) {
    if (!("sshPublicKey" in value) || value["sshPublicKey"] === void 0) return false;
    return true;
  }
  function SetupRootPasswordRequestFromJSON(json) {
    return SetupRootPasswordRequestFromJSONTyped(json, false);
  }
  function SetupRootPasswordRequestFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "sshPublicKey": json["ssh_public_key"],
      "requestTimeout": json["request_timeout"] == null ? void 0 : json["request_timeout"]
    };
  }
  function SetupRootPasswordRequestToJSON(json) {
    return SetupRootPasswordRequestToJSONTyped(json, false);
  }
  function SetupRootPasswordRequestToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "ssh_public_key": value["sshPublicKey"],
      "request_timeout": value["requestTimeout"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/SetupSandboxRequest.ts
  function instanceOfSetupSandboxRequest(value) {
    if (!("dataset" in value) || value["dataset"] === void 0) return false;
    if (!("platoDatasetConfig" in value) || value["platoDatasetConfig"] === void 0) return false;
    return true;
  }
  function SetupSandboxRequestFromJSON(json) {
    return SetupSandboxRequestFromJSONTyped(json, false);
  }
  function SetupSandboxRequestFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "service": json["service"] == null ? void 0 : json["service"],
      "dataset": json["dataset"],
      "platoDatasetConfig": SimConfigDatasetFromJSON(json["plato_dataset_config"]),
      "requestTimeout": json["request_timeout"] == null ? void 0 : json["request_timeout"],
      "sshPassword": json["ssh_password"] == null ? void 0 : json["ssh_password"],
      "sshPublicKey": json["ssh_public_key"] == null ? void 0 : json["ssh_public_key"]
    };
  }
  function SetupSandboxRequestToJSON(json) {
    return SetupSandboxRequestToJSONTyped(json, false);
  }
  function SetupSandboxRequestToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "service": value["service"],
      "dataset": value["dataset"],
      "plato_dataset_config": SimConfigDatasetToJSON(value["platoDatasetConfig"]),
      "request_timeout": value["requestTimeout"],
      "ssh_password": value["sshPassword"],
      "ssh_public_key": value["sshPublicKey"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/SetupSandboxResponse.ts
  function instanceOfSetupSandboxResponse(value) {
    if (!("status" in value) || value["status"] === void 0) return false;
    if (!("correlationId" in value) || value["correlationId"] === void 0) return false;
    if (!("sshUrl" in value) || value["sshUrl"] === void 0) return false;
    return true;
  }
  function SetupSandboxResponseFromJSON(json) {
    return SetupSandboxResponseFromJSONTyped(json, false);
  }
  function SetupSandboxResponseFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "status": json["status"],
      "timestamp": json["timestamp"] == null ? void 0 : json["timestamp"],
      "correlationId": json["correlation_id"],
      "sshUrl": json["ssh_url"]
    };
  }
  function SetupSandboxResponseToJSON(json) {
    return SetupSandboxResponseToJSONTyped(json, false);
  }
  function SetupSandboxResponseToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "status": value["status"],
      "timestamp": value["timestamp"],
      "correlation_id": value["correlationId"],
      "ssh_url": value["sshUrl"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/SimulatorListItem.ts
  function instanceOfSimulatorListItem(value) {
    if (!("id" in value) || value["id"] === void 0) return false;
    if (!("name" in value) || value["name"] === void 0) return false;
    if (!("enabled" in value) || value["enabled"] === void 0) return false;
    if (!("simType" in value) || value["simType"] === void 0) return false;
    if (!("versionTag" in value) || value["versionTag"] === void 0) return false;
    return true;
  }
  function SimulatorListItemFromJSON(json) {
    return SimulatorListItemFromJSONTyped(json, false);
  }
  function SimulatorListItemFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "id": json["id"],
      "name": json["name"],
      "description": json["description"] == null ? void 0 : json["description"],
      "imgUrl": json["img_url"] == null ? void 0 : json["img_url"],
      "enabled": json["enabled"],
      "simType": json["sim_type"],
      "jobName": json["job_name"] == null ? void 0 : json["job_name"],
      "internalAppPort": json["internal_app_port"] == null ? void 0 : json["internal_app_port"],
      "versionTag": json["version_tag"],
      "imageUri": json["image_uri"] == null ? void 0 : json["image_uri"]
    };
  }
  function SimulatorListItemToJSON(json) {
    return SimulatorListItemToJSONTyped(json, false);
  }
  function SimulatorListItemToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "id": value["id"],
      "name": value["name"],
      "description": value["description"],
      "img_url": value["imgUrl"],
      "enabled": value["enabled"],
      "sim_type": value["simType"],
      "job_name": value["jobName"],
      "internal_app_port": value["internalAppPort"],
      "version_tag": value["versionTag"],
      "image_uri": value["imageUri"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/SimulatorVersionDetails.ts
  function instanceOfSimulatorVersionDetails(value) {
    if (!("artifactId" in value) || value["artifactId"] === void 0) return false;
    if (!("version" in value) || value["version"] === void 0) return false;
    if (!("createdAt" in value) || value["createdAt"] === void 0) return false;
    if (!("workerImage" in value) || value["workerImage"] === void 0) return false;
    if (!("ecsTaskDefinitionArn" in value) || value["ecsTaskDefinitionArn"] === void 0) return false;
    if (!("snapshotS3Uri" in value) || value["snapshotS3Uri"] === void 0) return false;
    if (!("dataset" in value) || value["dataset"] === void 0) return false;
    return true;
  }
  function SimulatorVersionDetailsFromJSON(json) {
    return SimulatorVersionDetailsFromJSONTyped(json, false);
  }
  function SimulatorVersionDetailsFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "artifactId": json["artifact_id"],
      "version": json["version"],
      "createdAt": new Date(json["created_at"]),
      "workerImage": json["worker_image"],
      "ecsTaskDefinitionArn": json["ecs_task_definition_arn"],
      "snapshotS3Uri": json["snapshot_s3_uri"],
      "dataset": json["dataset"]
    };
  }
  function SimulatorVersionDetailsToJSON(json) {
    return SimulatorVersionDetailsToJSONTyped(json, false);
  }
  function SimulatorVersionDetailsToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "artifact_id": value["artifactId"],
      "version": value["version"],
      "created_at": value["createdAt"].toISOString(),
      "worker_image": value["workerImage"],
      "ecs_task_definition_arn": value["ecsTaskDefinitionArn"],
      "snapshot_s3_uri": value["snapshotS3Uri"],
      "dataset": value["dataset"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/SimulatorVersionsResponse.ts
  function instanceOfSimulatorVersionsResponse(value) {
    if (!("simulatorName" in value) || value["simulatorName"] === void 0) return false;
    if (!("versions" in value) || value["versions"] === void 0) return false;
    if (!("totalVersions" in value) || value["totalVersions"] === void 0) return false;
    return true;
  }
  function SimulatorVersionsResponseFromJSON(json) {
    return SimulatorVersionsResponseFromJSONTyped(json, false);
  }
  function SimulatorVersionsResponseFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "simulatorName": json["simulator_name"],
      "versions": json["versions"].map(SimulatorVersionDetailsFromJSON),
      "totalVersions": json["total_versions"]
    };
  }
  function SimulatorVersionsResponseToJSON(json) {
    return SimulatorVersionsResponseToJSONTyped(json, false);
  }
  function SimulatorVersionsResponseToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "simulator_name": value["simulatorName"],
      "versions": value["versions"].map(SimulatorVersionDetailsToJSON),
      "total_versions": value["totalVersions"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/VMManagementRequest.ts
  function instanceOfVMManagementRequest(value) {
    if (!("dataset" in value) || value["dataset"] === void 0) return false;
    if (!("platoDatasetConfig" in value) || value["platoDatasetConfig"] === void 0) return false;
    return true;
  }
  function VMManagementRequestFromJSON(json) {
    return VMManagementRequestFromJSONTyped(json, false);
  }
  function VMManagementRequestFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "service": json["service"] == null ? void 0 : json["service"],
      "dataset": json["dataset"],
      "platoDatasetConfig": SimConfigDatasetFromJSON(json["plato_dataset_config"]),
      "requestTimeout": json["request_timeout"] == null ? void 0 : json["request_timeout"]
    };
  }
  function VMManagementRequestToJSON(json) {
    return VMManagementRequestToJSONTyped(json, false);
  }
  function VMManagementRequestToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "service": value["service"],
      "dataset": value["dataset"],
      "plato_dataset_config": SimConfigDatasetToJSON(value["platoDatasetConfig"]),
      "request_timeout": value["requestTimeout"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/VMManagementResponse.ts
  function instanceOfVMManagementResponse(value) {
    if (!("status" in value) || value["status"] === void 0) return false;
    if (!("correlationId" in value) || value["correlationId"] === void 0) return false;
    return true;
  }
  function VMManagementResponseFromJSON(json) {
    return VMManagementResponseFromJSONTyped(json, false);
  }
  function VMManagementResponseFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "status": json["status"],
      "timestamp": json["timestamp"] == null ? void 0 : json["timestamp"],
      "correlationId": json["correlation_id"]
    };
  }
  function VMManagementResponseToJSON(json) {
    return VMManagementResponseToJSONTyped(json, false);
  }
  function VMManagementResponseToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "status": value["status"],
      "timestamp": value["timestamp"],
      "correlation_id": value["correlationId"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/WorkerReadyResponse.ts
  function instanceOfWorkerReadyResponse(value) {
    if (!("ready" in value) || value["ready"] === void 0) return false;
    return true;
  }
  function WorkerReadyResponseFromJSON(json) {
    return WorkerReadyResponseFromJSONTyped(json, false);
  }
  function WorkerReadyResponseFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "ready": json["ready"],
      "jobId": json["job_id"] == null ? void 0 : json["job_id"],
      "workerPrivateIp": json["worker_private_ip"] == null ? void 0 : json["worker_private_ip"],
      "workerPublicIp": json["worker_public_ip"] == null ? void 0 : json["worker_public_ip"],
      "meshIp": json["mesh_ip"] == null ? void 0 : json["mesh_ip"],
      "workerPort": json["worker_port"] == null ? void 0 : json["worker_port"],
      "healthStatus": json["health_status"] == null ? void 0 : json["health_status"],
      "error": json["error"] == null ? void 0 : json["error"]
    };
  }
  function WorkerReadyResponseToJSON(json) {
    return WorkerReadyResponseToJSONTyped(json, false);
  }
  function WorkerReadyResponseToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "ready": value["ready"],
      "job_id": value["jobId"],
      "worker_private_ip": value["workerPrivateIp"],
      "worker_public_ip": value["workerPublicIp"],
      "mesh_ip": value["meshIp"],
      "worker_port": value["workerPort"],
      "health_status": value["healthStatus"],
      "error": value["error"]
    };
  }

  // ../../sdk/typescript-sdk/src/apis/EnvApi.ts
  var EnvApi = class extends BaseAPI {
    /**
     * Create a backup of the environment.
     * Backup Env
     */
    async backupEnvironmentRaw(requestParameters, initOverrides) {
      if (requestParameters["jobGroupId"] == null) {
        throw new RequiredError(
          "jobGroupId",
          'Required parameter "jobGroupId" was null or undefined when calling backupEnvironment().'
        );
      }
      const queryParameters = {};
      const headerParameters = {};
      if (requestParameters["authorization"] != null) {
        headerParameters["authorization"] = String(requestParameters["authorization"]);
      }
      if (requestParameters["xInternalService"] != null) {
        headerParameters["X-Internal-Service"] = String(requestParameters["xInternalService"]);
      }
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/env/{job_group_id}/backup`;
      urlPath = urlPath.replace(`{${"job_group_id"}}`, encodeURIComponent(String(requestParameters["jobGroupId"])));
      const response = await this.request({
        path: urlPath,
        method: "POST",
        headers: headerParameters,
        query: queryParameters
      }, initOverrides);
      return new JSONApiResponse(response);
    }
    /**
     * Create a backup of the environment.
     * Backup Env
     */
    async backupEnvironment(requestParameters, initOverrides) {
      const response = await this.backupEnvironmentRaw(requestParameters, initOverrides);
      return await response.value();
    }
    /**
     * Close Env
     */
    async closeEnvironmentRaw(requestParameters, initOverrides) {
      if (requestParameters["jobGroupId"] == null) {
        throw new RequiredError(
          "jobGroupId",
          'Required parameter "jobGroupId" was null or undefined when calling closeEnvironment().'
        );
      }
      const queryParameters = {};
      const headerParameters = {};
      if (requestParameters["authorization"] != null) {
        headerParameters["authorization"] = String(requestParameters["authorization"]);
      }
      if (requestParameters["xInternalService"] != null) {
        headerParameters["X-Internal-Service"] = String(requestParameters["xInternalService"]);
      }
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/env/{job_group_id}/close`;
      urlPath = urlPath.replace(`{${"job_group_id"}}`, encodeURIComponent(String(requestParameters["jobGroupId"])));
      const response = await this.request({
        path: urlPath,
        method: "POST",
        headers: headerParameters,
        query: queryParameters
      }, initOverrides);
      return new JSONApiResponse(response);
    }
    /**
     * Close Env
     */
    async closeEnvironment(requestParameters, initOverrides) {
      const response = await this.closeEnvironmentRaw(requestParameters, initOverrides);
      return await response.value();
    }
    /**
     * Create a new simulator.
     * Create Simulator
     */
    async createSimulatorRaw(requestParameters, initOverrides) {
      if (requestParameters["createSimulatorRequest"] == null) {
        throw new RequiredError(
          "createSimulatorRequest",
          'Required parameter "createSimulatorRequest" was null or undefined when calling createSimulator().'
        );
      }
      const queryParameters = {};
      const headerParameters = {};
      headerParameters["Content-Type"] = "application/json";
      if (requestParameters["authorization"] != null) {
        headerParameters["authorization"] = String(requestParameters["authorization"]);
      }
      if (requestParameters["xInternalService"] != null) {
        headerParameters["X-Internal-Service"] = String(requestParameters["xInternalService"]);
      }
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/env/simulators`;
      const response = await this.request({
        path: urlPath,
        method: "POST",
        headers: headerParameters,
        query: queryParameters,
        body: CreateSimulatorRequestToJSON(requestParameters["createSimulatorRequest"])
      }, initOverrides);
      return new JSONApiResponse(response);
    }
    /**
     * Create a new simulator.
     * Create Simulator
     */
    async createSimulator(requestParameters, initOverrides) {
      const response = await this.createSimulatorRaw(requestParameters, initOverrides);
      return await response.value();
    }
    /**
     * Evaluate the session.
     * Evaluate Session
     */
    async evaluateSessionRaw(requestParameters, initOverrides) {
      if (requestParameters["sessionId"] == null) {
        throw new RequiredError(
          "sessionId",
          'Required parameter "sessionId" was null or undefined when calling evaluateSession().'
        );
      }
      const queryParameters = {};
      const headerParameters = {};
      headerParameters["Content-Type"] = "application/json";
      if (requestParameters["authorization"] != null) {
        headerParameters["authorization"] = String(requestParameters["authorization"]);
      }
      if (requestParameters["xInternalService"] != null) {
        headerParameters["X-Internal-Service"] = String(requestParameters["xInternalService"]);
      }
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/env/session/{session_id}/evaluate`;
      urlPath = urlPath.replace(`{${"session_id"}}`, encodeURIComponent(String(requestParameters["sessionId"])));
      const response = await this.request({
        path: urlPath,
        method: "POST",
        headers: headerParameters,
        query: queryParameters,
        body: EvaluateRequestToJSON(requestParameters["evaluateRequest"])
      }, initOverrides);
      return new JSONApiResponse(response);
    }
    /**
     * Evaluate the session.
     * Evaluate Session
     */
    async evaluateSession(requestParameters, initOverrides) {
      const response = await this.evaluateSessionRaw(requestParameters, initOverrides);
      return await response.value();
    }
    /**
     * Get the active session for a job group.
     * Get Active Session
     */
    async getActiveSessionRaw(requestParameters, initOverrides) {
      if (requestParameters["jobGroupId"] == null) {
        throw new RequiredError(
          "jobGroupId",
          'Required parameter "jobGroupId" was null or undefined when calling getActiveSession().'
        );
      }
      const queryParameters = {};
      const headerParameters = {};
      if (requestParameters["authorization"] != null) {
        headerParameters["authorization"] = String(requestParameters["authorization"]);
      }
      if (requestParameters["xInternalService"] != null) {
        headerParameters["X-Internal-Service"] = String(requestParameters["xInternalService"]);
      }
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/env/{job_group_id}/active_session`;
      urlPath = urlPath.replace(`{${"job_group_id"}}`, encodeURIComponent(String(requestParameters["jobGroupId"])));
      const response = await this.request({
        path: urlPath,
        method: "GET",
        headers: headerParameters,
        query: queryParameters
      }, initOverrides);
      return new JSONApiResponse(response);
    }
    /**
     * Get the active session for a job group.
     * Get Active Session
     */
    async getActiveSession(requestParameters, initOverrides) {
      const response = await this.getActiveSessionRaw(requestParameters, initOverrides);
      return await response.value();
    }
    /**
     * Get the CDP URL for the environment.
     * Get Cdp Url
     */
    async getCdpUrlRaw(requestParameters, initOverrides) {
      if (requestParameters["jobGroupId"] == null) {
        throw new RequiredError(
          "jobGroupId",
          'Required parameter "jobGroupId" was null or undefined when calling getCdpUrl().'
        );
      }
      const queryParameters = {};
      const headerParameters = {};
      if (requestParameters["authorization"] != null) {
        headerParameters["authorization"] = String(requestParameters["authorization"]);
      }
      if (requestParameters["xInternalService"] != null) {
        headerParameters["X-Internal-Service"] = String(requestParameters["xInternalService"]);
      }
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/env/{job_group_id}/cdp_url`;
      urlPath = urlPath.replace(`{${"job_group_id"}}`, encodeURIComponent(String(requestParameters["jobGroupId"])));
      const response = await this.request({
        path: urlPath,
        method: "GET",
        headers: headerParameters,
        query: queryParameters
      }, initOverrides);
      return new JSONApiResponse(response);
    }
    /**
     * Get the CDP URL for the environment.
     * Get Cdp Url
     */
    async getCdpUrl(requestParameters, initOverrides) {
      const response = await this.getCdpUrlRaw(requestParameters, initOverrides);
      return await response.value();
    }
    /**
     * Get Env State
     */
    async getEnvironmentStateRaw(requestParameters, initOverrides) {
      if (requestParameters["jobGroupId"] == null) {
        throw new RequiredError(
          "jobGroupId",
          'Required parameter "jobGroupId" was null or undefined when calling getEnvironmentState().'
        );
      }
      const queryParameters = {};
      const headerParameters = {};
      if (requestParameters["authorization"] != null) {
        headerParameters["authorization"] = String(requestParameters["authorization"]);
      }
      if (requestParameters["xInternalService"] != null) {
        headerParameters["X-Internal-Service"] = String(requestParameters["xInternalService"]);
      }
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/env/{job_group_id}/state`;
      urlPath = urlPath.replace(`{${"job_group_id"}}`, encodeURIComponent(String(requestParameters["jobGroupId"])));
      const response = await this.request({
        path: urlPath,
        method: "GET",
        headers: headerParameters,
        query: queryParameters
      }, initOverrides);
      return new JSONApiResponse(response);
    }
    /**
     * Get Env State
     */
    async getEnvironmentState(requestParameters, initOverrides) {
      const response = await this.getEnvironmentStateRaw(requestParameters, initOverrides);
      return await response.value();
    }
    /**
     * Get Job Status
     */
    async getJobStatusRaw(requestParameters, initOverrides) {
      if (requestParameters["jobGroupId"] == null) {
        throw new RequiredError(
          "jobGroupId",
          'Required parameter "jobGroupId" was null or undefined when calling getJobStatus().'
        );
      }
      const queryParameters = {};
      const headerParameters = {};
      if (requestParameters["authorization"] != null) {
        headerParameters["authorization"] = String(requestParameters["authorization"]);
      }
      if (requestParameters["xInternalService"] != null) {
        headerParameters["X-Internal-Service"] = String(requestParameters["xInternalService"]);
      }
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/env/{job_group_id}/status`;
      urlPath = urlPath.replace(`{${"job_group_id"}}`, encodeURIComponent(String(requestParameters["jobGroupId"])));
      const response = await this.request({
        path: urlPath,
        method: "GET",
        headers: headerParameters,
        query: queryParameters
      }, initOverrides);
      return new JSONApiResponse(response, (jsonValue) => JobStatusResponseFromJSON(jsonValue));
    }
    /**
     * Get Job Status
     */
    async getJobStatus(requestParameters, initOverrides) {
      const response = await this.getJobStatusRaw(requestParameters, initOverrides);
      return await response.value();
    }
    /**
     * Get the public URL for the environment.
     * Get Proxy Url
     */
    async getProxyUrlRaw(requestParameters, initOverrides) {
      if (requestParameters["jobGroupId"] == null) {
        throw new RequiredError(
          "jobGroupId",
          'Required parameter "jobGroupId" was null or undefined when calling getProxyUrl().'
        );
      }
      const queryParameters = {};
      const headerParameters = {};
      if (requestParameters["authorization"] != null) {
        headerParameters["authorization"] = String(requestParameters["authorization"]);
      }
      if (requestParameters["xInternalService"] != null) {
        headerParameters["X-Internal-Service"] = String(requestParameters["xInternalService"]);
      }
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/env/{job_group_id}/proxy_url`;
      urlPath = urlPath.replace(`{${"job_group_id"}}`, encodeURIComponent(String(requestParameters["jobGroupId"])));
      const response = await this.request({
        path: urlPath,
        method: "GET",
        headers: headerParameters,
        query: queryParameters
      }, initOverrides);
      return new JSONApiResponse(response);
    }
    /**
     * Get the public URL for the environment.
     * Get Proxy Url
     */
    async getProxyUrl(requestParameters, initOverrides) {
      const response = await this.getProxyUrlRaw(requestParameters, initOverrides);
      return await response.value();
    }
    /**
     * Get all simulators with optimized queries.
     * Get Simulators
     */
    async getSimulatorsRaw(requestParameters, initOverrides) {
      const queryParameters = {};
      const headerParameters = {};
      if (requestParameters["authorization"] != null) {
        headerParameters["authorization"] = String(requestParameters["authorization"]);
      }
      if (requestParameters["xInternalService"] != null) {
        headerParameters["X-Internal-Service"] = String(requestParameters["xInternalService"]);
      }
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/env/simulators`;
      const response = await this.request({
        path: urlPath,
        method: "GET",
        headers: headerParameters,
        query: queryParameters
      }, initOverrides);
      return new JSONApiResponse(response);
    }
    /**
     * Get all simulators with optimized queries.
     * Get Simulators
     */
    async getSimulators(requestParameters = {}, initOverrides) {
      const response = await this.getSimulatorsRaw(requestParameters, initOverrides);
      return await response.value();
    }
    /**
     * Check if the workers for this job group are ready and healthy.  Uses the persistent job ready notification service to wait for job readiness. Falls back to checking Redis if notification not received (in case we missed it). Raises 500 if job not ready after all checks. 
     * Get Worker Ready
     */
    async getWorkerReadyApiEnvJobIdWorkerReadyGetRaw(requestParameters, initOverrides) {
      if (requestParameters["jobId"] == null) {
        throw new RequiredError(
          "jobId",
          'Required parameter "jobId" was null or undefined when calling getWorkerReadyApiEnvJobIdWorkerReadyGet().'
        );
      }
      const queryParameters = {};
      if (requestParameters["timeout"] != null) {
        queryParameters["timeout"] = requestParameters["timeout"];
      }
      const headerParameters = {};
      if (requestParameters["authorization"] != null) {
        headerParameters["authorization"] = String(requestParameters["authorization"]);
      }
      if (requestParameters["xInternalService"] != null) {
        headerParameters["X-Internal-Service"] = String(requestParameters["xInternalService"]);
      }
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/env/{job_id}/worker_ready`;
      urlPath = urlPath.replace(`{${"job_id"}}`, encodeURIComponent(String(requestParameters["jobId"])));
      const response = await this.request({
        path: urlPath,
        method: "GET",
        headers: headerParameters,
        query: queryParameters
      }, initOverrides);
      return new JSONApiResponse(response, (jsonValue) => WorkerReadyResponseFromJSON(jsonValue));
    }
    /**
     * Check if the workers for this job group are ready and healthy.  Uses the persistent job ready notification service to wait for job readiness. Falls back to checking Redis if notification not received (in case we missed it). Raises 500 if job not ready after all checks. 
     * Get Worker Ready
     */
    async getWorkerReadyApiEnvJobIdWorkerReadyGet(requestParameters, initOverrides) {
      const response = await this.getWorkerReadyApiEnvJobIdWorkerReadyGetRaw(requestParameters, initOverrides);
      return await response.value();
    }
    /**
     * Log a state mutation or batch of mutations.
     * Log State Mutation
     */
    async logStateMutationApiEnvSessionIdLogPostRaw(requestParameters, initOverrides) {
      if (requestParameters["sessionId"] == null) {
        throw new RequiredError(
          "sessionId",
          'Required parameter "sessionId" was null or undefined when calling logStateMutationApiEnvSessionIdLogPost().'
        );
      }
      if (requestParameters["log"] == null) {
        throw new RequiredError(
          "log",
          'Required parameter "log" was null or undefined when calling logStateMutationApiEnvSessionIdLogPost().'
        );
      }
      const queryParameters = {};
      const headerParameters = {};
      headerParameters["Content-Type"] = "application/json";
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/env/{session_id}/log`;
      urlPath = urlPath.replace(`{${"session_id"}}`, encodeURIComponent(String(requestParameters["sessionId"])));
      const response = await this.request({
        path: urlPath,
        method: "POST",
        headers: headerParameters,
        query: queryParameters,
        body: LogToJSON(requestParameters["log"])
      }, initOverrides);
      return new JSONApiResponse(response);
    }
    /**
     * Log a state mutation or batch of mutations.
     * Log State Mutation
     */
    async logStateMutationApiEnvSessionIdLogPost(requestParameters, initOverrides) {
      const response = await this.logStateMutationApiEnvSessionIdLogPostRaw(requestParameters, initOverrides);
      return await response.value();
    }
    /**
     * Make Env
     */
    async makeEnvironmentRaw(requestParameters, initOverrides) {
      if (requestParameters["makeEnvRequest2"] == null) {
        throw new RequiredError(
          "makeEnvRequest2",
          'Required parameter "makeEnvRequest2" was null or undefined when calling makeEnvironment().'
        );
      }
      const queryParameters = {};
      const headerParameters = {};
      headerParameters["Content-Type"] = "application/json";
      if (requestParameters["authorization"] != null) {
        headerParameters["authorization"] = String(requestParameters["authorization"]);
      }
      if (requestParameters["xInternalService"] != null) {
        headerParameters["X-Internal-Service"] = String(requestParameters["xInternalService"]);
      }
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/env/make2`;
      const response = await this.request({
        path: urlPath,
        method: "POST",
        headers: headerParameters,
        query: queryParameters,
        body: MakeEnvRequest2ToJSON(requestParameters["makeEnvRequest2"])
      }, initOverrides);
      return new JSONApiResponse(response);
    }
    /**
     * Make Env
     */
    async makeEnvironment(requestParameters, initOverrides) {
      const response = await this.makeEnvironmentRaw(requestParameters, initOverrides);
      return await response.value();
    }
    /**
     * Reset the environment with an optional task.
     * Reset Env
     */
    async resetEnvironmentRaw(requestParameters, initOverrides) {
      if (requestParameters["jobGroupId"] == null) {
        throw new RequiredError(
          "jobGroupId",
          'Required parameter "jobGroupId" was null or undefined when calling resetEnvironment().'
        );
      }
      if (requestParameters["resetEnvRequest"] == null) {
        throw new RequiredError(
          "resetEnvRequest",
          'Required parameter "resetEnvRequest" was null or undefined when calling resetEnvironment().'
        );
      }
      const queryParameters = {};
      const headerParameters = {};
      headerParameters["Content-Type"] = "application/json";
      if (requestParameters["authorization"] != null) {
        headerParameters["authorization"] = String(requestParameters["authorization"]);
      }
      if (requestParameters["xInternalService"] != null) {
        headerParameters["X-Internal-Service"] = String(requestParameters["xInternalService"]);
      }
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/env/{job_group_id}/reset`;
      urlPath = urlPath.replace(`{${"job_group_id"}}`, encodeURIComponent(String(requestParameters["jobGroupId"])));
      const response = await this.request({
        path: urlPath,
        method: "POST",
        headers: headerParameters,
        query: queryParameters,
        body: ResetEnvRequestToJSON(requestParameters["resetEnvRequest"])
      }, initOverrides);
      return new JSONApiResponse(response);
    }
    /**
     * Reset the environment with an optional task.
     * Reset Env
     */
    async resetEnvironment(requestParameters, initOverrides) {
      const response = await this.resetEnvironmentRaw(requestParameters, initOverrides);
      return await response.value();
    }
    /**
     * Score the environment.
     * Score Env
     */
    async scoreEnvApiEnvSessionSessionIdScorePostRaw(requestParameters, initOverrides) {
      if (requestParameters["sessionId"] == null) {
        throw new RequiredError(
          "sessionId",
          'Required parameter "sessionId" was null or undefined when calling scoreEnvApiEnvSessionSessionIdScorePost().'
        );
      }
      if (requestParameters["scoreRequest"] == null) {
        throw new RequiredError(
          "scoreRequest",
          'Required parameter "scoreRequest" was null or undefined when calling scoreEnvApiEnvSessionSessionIdScorePost().'
        );
      }
      const queryParameters = {};
      const headerParameters = {};
      headerParameters["Content-Type"] = "application/json";
      if (requestParameters["authorization"] != null) {
        headerParameters["authorization"] = String(requestParameters["authorization"]);
      }
      if (requestParameters["xInternalService"] != null) {
        headerParameters["X-Internal-Service"] = String(requestParameters["xInternalService"]);
      }
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/env/session/{session_id}/score`;
      urlPath = urlPath.replace(`{${"session_id"}}`, encodeURIComponent(String(requestParameters["sessionId"])));
      const response = await this.request({
        path: urlPath,
        method: "POST",
        headers: headerParameters,
        query: queryParameters,
        body: ScoreRequestToJSON(requestParameters["scoreRequest"])
      }, initOverrides);
      return new JSONApiResponse(response);
    }
    /**
     * Score the environment.
     * Score Env
     */
    async scoreEnvApiEnvSessionSessionIdScorePost(requestParameters, initOverrides) {
      const response = await this.scoreEnvApiEnvSessionSessionIdScorePostRaw(requestParameters, initOverrides);
      return await response.value();
    }
    /**
     * Send a heartbeat to keep the environment session alive.
     * Send Heartbeat
     */
    async sendHeartbeatRaw(requestParameters, initOverrides) {
      if (requestParameters["jobId"] == null) {
        throw new RequiredError(
          "jobId",
          'Required parameter "jobId" was null or undefined when calling sendHeartbeat().'
        );
      }
      const queryParameters = {};
      const headerParameters = {};
      if (requestParameters["authorization"] != null) {
        headerParameters["authorization"] = String(requestParameters["authorization"]);
      }
      if (requestParameters["xInternalService"] != null) {
        headerParameters["X-Internal-Service"] = String(requestParameters["xInternalService"]);
      }
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/env/{job_id}/heartbeat`;
      urlPath = urlPath.replace(`{${"job_id"}}`, encodeURIComponent(String(requestParameters["jobId"])));
      const response = await this.request({
        path: urlPath,
        method: "POST",
        headers: headerParameters,
        query: queryParameters
      }, initOverrides);
      return new JSONApiResponse(response);
    }
    /**
     * Send a heartbeat to keep the environment session alive.
     * Send Heartbeat
     */
    async sendHeartbeat(requestParameters, initOverrides) {
      const response = await this.sendHeartbeatRaw(requestParameters, initOverrides);
      return await response.value();
    }
  };

  // ../../sdk/typescript-sdk/src/apis/GiteaApi.ts
  var GiteaApi = class extends BaseAPI {
    /**
     * Create a repository for a simulator (only if it doesn\'t exist)
     * Create Simulator Repository
     */
    async createSimulatorRepositoryRaw(requestParameters, initOverrides) {
      if (requestParameters["simulatorId"] == null) {
        throw new RequiredError(
          "simulatorId",
          'Required parameter "simulatorId" was null or undefined when calling createSimulatorRepository().'
        );
      }
      const queryParameters = {};
      const headerParameters = {};
      if (requestParameters["authorization"] != null) {
        headerParameters["authorization"] = String(requestParameters["authorization"]);
      }
      if (requestParameters["xInternalService"] != null) {
        headerParameters["X-Internal-Service"] = String(requestParameters["xInternalService"]);
      }
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/gitea/simulators/{simulator_id}/repo`;
      urlPath = urlPath.replace(`{${"simulator_id"}}`, encodeURIComponent(String(requestParameters["simulatorId"])));
      const response = await this.request({
        path: urlPath,
        method: "POST",
        headers: headerParameters,
        query: queryParameters
      }, initOverrides);
      return new JSONApiResponse(response);
    }
    /**
     * Create a repository for a simulator (only if it doesn\'t exist)
     * Create Simulator Repository
     */
    async createSimulatorRepository(requestParameters, initOverrides) {
      const response = await this.createSimulatorRepositoryRaw(requestParameters, initOverrides);
      return await response.value();
    }
    /**
     * Get simulators that user has access to view repos for
     * Get Accessible Simulators
     */
    async getAccessibleSimulatorsRaw(requestParameters, initOverrides) {
      const queryParameters = {};
      const headerParameters = {};
      if (requestParameters["authorization"] != null) {
        headerParameters["authorization"] = String(requestParameters["authorization"]);
      }
      if (requestParameters["xInternalService"] != null) {
        headerParameters["X-Internal-Service"] = String(requestParameters["xInternalService"]);
      }
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/gitea/simulators`;
      const response = await this.request({
        path: urlPath,
        method: "GET",
        headers: headerParameters,
        query: queryParameters
      }, initOverrides);
      return new JSONApiResponse(response);
    }
    /**
     * Get simulators that user has access to view repos for
     * Get Accessible Simulators
     */
    async getAccessibleSimulators(requestParameters = {}, initOverrides) {
      const response = await this.getAccessibleSimulatorsRaw(requestParameters, initOverrides);
      return await response.value();
    }
    /**
     * Get Gitea credentials for the organization
     * Get Gitea Credentials
     */
    async getGiteaCredentialsRaw(requestParameters, initOverrides) {
      const queryParameters = {};
      const headerParameters = {};
      if (requestParameters["authorization"] != null) {
        headerParameters["authorization"] = String(requestParameters["authorization"]);
      }
      if (requestParameters["xInternalService"] != null) {
        headerParameters["X-Internal-Service"] = String(requestParameters["xInternalService"]);
      }
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/gitea/credentials`;
      const response = await this.request({
        path: urlPath,
        method: "GET",
        headers: headerParameters,
        query: queryParameters
      }, initOverrides);
      return new JSONApiResponse(response);
    }
    /**
     * Get Gitea credentials for the organization
     * Get Gitea Credentials
     */
    async getGiteaCredentials(requestParameters = {}, initOverrides) {
      const response = await this.getGiteaCredentialsRaw(requestParameters, initOverrides);
      return await response.value();
    }
    /**
     * Get the current user\'s Gitea info (auto-provisions if needed)
     * Get My Gitea Info
     */
    async getMyGiteaInfoRaw(requestParameters, initOverrides) {
      const queryParameters = {};
      const headerParameters = {};
      if (requestParameters["authorization"] != null) {
        headerParameters["authorization"] = String(requestParameters["authorization"]);
      }
      if (requestParameters["xInternalService"] != null) {
        headerParameters["X-Internal-Service"] = String(requestParameters["xInternalService"]);
      }
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/gitea/my-info`;
      const response = await this.request({
        path: urlPath,
        method: "GET",
        headers: headerParameters,
        query: queryParameters
      }, initOverrides);
      return new JSONApiResponse(response);
    }
    /**
     * Get the current user\'s Gitea info (auto-provisions if needed)
     * Get My Gitea Info
     */
    async getMyGiteaInfo(requestParameters = {}, initOverrides) {
      const response = await this.getMyGiteaInfoRaw(requestParameters, initOverrides);
      return await response.value();
    }
    /**
     * Get repository details for a specific simulator
     * Get Simulator Repository
     */
    async getSimulatorRepositoryRaw(requestParameters, initOverrides) {
      if (requestParameters["simulatorId"] == null) {
        throw new RequiredError(
          "simulatorId",
          'Required parameter "simulatorId" was null or undefined when calling getSimulatorRepository().'
        );
      }
      const queryParameters = {};
      const headerParameters = {};
      if (requestParameters["authorization"] != null) {
        headerParameters["authorization"] = String(requestParameters["authorization"]);
      }
      if (requestParameters["xInternalService"] != null) {
        headerParameters["X-Internal-Service"] = String(requestParameters["xInternalService"]);
      }
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/gitea/simulators/{simulator_id}/repo`;
      urlPath = urlPath.replace(`{${"simulator_id"}}`, encodeURIComponent(String(requestParameters["simulatorId"])));
      const response = await this.request({
        path: urlPath,
        method: "GET",
        headers: headerParameters,
        query: queryParameters
      }, initOverrides);
      return new JSONApiResponse(response);
    }
    /**
     * Get repository details for a specific simulator
     * Get Simulator Repository
     */
    async getSimulatorRepository(requestParameters, initOverrides) {
      const response = await this.getSimulatorRepositoryRaw(requestParameters, initOverrides);
      return await response.value();
    }
  };

  // ../../sdk/typescript-sdk/src/apis/PublicBuildApi.ts
  var PublicBuildApi = class extends BaseAPI {
    /**
     * Create a checkpoint snapshot of a VM.  This creates a blockdiff_checkpoint artifact type instead of a regular blockdiff. Optional parameters allow overriding artifact labels: - service: Simulator name (defaults to job\'s service) - git_hash: Git hash/version (defaults to job\'s version or \"unknown\") - dataset: Dataset name (defaults to job\'s dataset) 
     * Checkpoint Vm
     */
    async checkpointVMRaw(requestParameters, initOverrides) {
      if (requestParameters["publicId"] == null) {
        throw new RequiredError(
          "publicId",
          'Required parameter "publicId" was null or undefined when calling checkpointVM().'
        );
      }
      const queryParameters = {};
      const headerParameters = {};
      headerParameters["Content-Type"] = "application/json";
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/public-build/vm/{public_id}/checkpoint`;
      urlPath = urlPath.replace(`{${"public_id"}}`, encodeURIComponent(String(requestParameters["publicId"])));
      const response = await this.request({
        path: urlPath,
        method: "POST",
        headers: headerParameters,
        query: queryParameters,
        body: CreateSnapshotRequestToJSON(requestParameters["createSnapshotRequest"])
      }, initOverrides);
      return new JSONApiResponse(response, (jsonValue) => CreateSnapshotResponseFromJSON(jsonValue));
    }
    /**
     * Create a checkpoint snapshot of a VM.  This creates a blockdiff_checkpoint artifact type instead of a regular blockdiff. Optional parameters allow overriding artifact labels: - service: Simulator name (defaults to job\'s service) - git_hash: Git hash/version (defaults to job\'s version or \"unknown\") - dataset: Dataset name (defaults to job\'s dataset) 
     * Checkpoint Vm
     */
    async checkpointVM(requestParameters, initOverrides) {
      const response = await this.checkpointVMRaw(requestParameters, initOverrides);
      return await response.value();
    }
    /**
     * Close and terminate a VM.
     * Close Vm
     */
    async closeVMRaw(requestParameters, initOverrides) {
      if (requestParameters["publicId"] == null) {
        throw new RequiredError(
          "publicId",
          'Required parameter "publicId" was null or undefined when calling closeVM().'
        );
      }
      const queryParameters = {};
      const headerParameters = {};
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/public-build/vm/{public_id}`;
      urlPath = urlPath.replace(`{${"public_id"}}`, encodeURIComponent(String(requestParameters["publicId"])));
      const response = await this.request({
        path: urlPath,
        method: "DELETE",
        headers: headerParameters,
        query: queryParameters
      }, initOverrides);
      return new JSONApiResponse(response, (jsonValue) => VMManagementResponseFromJSON(jsonValue));
    }
    /**
     * Close and terminate a VM.
     * Close Vm
     */
    async closeVM(requestParameters, initOverrides) {
      const response = await this.closeVMRaw(requestParameters, initOverrides);
      return await response.value();
    }
    /**
     * Create Vm
     */
    async createVMRaw(requestParameters, initOverrides) {
      if (requestParameters["createVMRequest"] == null) {
        throw new RequiredError(
          "createVMRequest",
          'Required parameter "createVMRequest" was null or undefined when calling createVM().'
        );
      }
      const queryParameters = {};
      const headerParameters = {};
      headerParameters["Content-Type"] = "application/json";
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/public-build/vm/create`;
      const response = await this.request({
        path: urlPath,
        method: "POST",
        headers: headerParameters,
        query: queryParameters,
        body: CreateVMRequestToJSON(requestParameters["createVMRequest"])
      }, initOverrides);
      return new JSONApiResponse(response, (jsonValue) => CreateVMResponseFromJSON(jsonValue));
    }
    /**
     * Create Vm
     */
    async createVM(requestParameters, initOverrides) {
      const response = await this.createVMRaw(requestParameters, initOverrides);
      return await response.value();
    }
    /**
     * Stream operation results via Server-Sent Events (SSE) for public usage.  Returns a stream of events with the following format: - event: Event type (e.g., \"connected\", \"progress\", \"complete\", \"error\") - data: JSON payload with event details  Events: - connected: Initial connection established - progress: Operation progress update - complete: Operation completed successfully - error: Operation failed with error details 
     * Get Operation Events
     */
    async getOperationEventsRaw(requestParameters, initOverrides) {
      if (requestParameters["correlationId"] == null) {
        throw new RequiredError(
          "correlationId",
          'Required parameter "correlationId" was null or undefined when calling getOperationEvents().'
        );
      }
      const queryParameters = {};
      const headerParameters = {};
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/public-build/events/{correlation_id}`;
      urlPath = urlPath.replace(`{${"correlation_id"}}`, encodeURIComponent(String(requestParameters["correlationId"])));
      const response = await this.request({
        path: urlPath,
        method: "GET",
        headers: headerParameters,
        query: queryParameters
      }, initOverrides);
      return new JSONApiResponse(response, (jsonValue) => GetOperationEvents200ResponseFromJSON(jsonValue));
    }
    /**
     * Stream operation results via Server-Sent Events (SSE) for public usage.  Returns a stream of events with the following format: - event: Event type (e.g., \"connected\", \"progress\", \"complete\", \"error\") - data: JSON payload with event details  Events: - connected: Initial connection established - progress: Operation progress update - complete: Operation completed successfully - error: Operation failed with error details 
     * Get Operation Events
     */
    async getOperationEvents(requestParameters, initOverrides) {
      const response = await this.getOperationEventsRaw(requestParameters, initOverrides);
      return await response.value();
    }
    /**
     * Save a snapshot of a VM.  Optional parameters allow overriding artifact labels: - service: Simulator name (defaults to job\'s service) - git_hash: Git hash/version (defaults to job\'s version or \"unknown\") - dataset: Dataset name (defaults to job\'s dataset) 
     * Save Vm Snapshot
     */
    async saveVmSnapshotApiPublicBuildVmPublicIdSnapshotPostRaw(requestParameters, initOverrides) {
      if (requestParameters["publicId"] == null) {
        throw new RequiredError(
          "publicId",
          'Required parameter "publicId" was null or undefined when calling saveVmSnapshotApiPublicBuildVmPublicIdSnapshotPost().'
        );
      }
      const queryParameters = {};
      const headerParameters = {};
      headerParameters["Content-Type"] = "application/json";
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/public-build/vm/{public_id}/snapshot`;
      urlPath = urlPath.replace(`{${"public_id"}}`, encodeURIComponent(String(requestParameters["publicId"])));
      const response = await this.request({
        path: urlPath,
        method: "POST",
        headers: headerParameters,
        query: queryParameters,
        body: CreateSnapshotRequestToJSON(requestParameters["createSnapshotRequest"])
      }, initOverrides);
      return new JSONApiResponse(response, (jsonValue) => CreateSnapshotResponseFromJSON(jsonValue));
    }
    /**
     * Save a snapshot of a VM.  Optional parameters allow overriding artifact labels: - service: Simulator name (defaults to job\'s service) - git_hash: Git hash/version (defaults to job\'s version or \"unknown\") - dataset: Dataset name (defaults to job\'s dataset) 
     * Save Vm Snapshot
     */
    async saveVmSnapshotApiPublicBuildVmPublicIdSnapshotPost(requestParameters, initOverrides) {
      const response = await this.saveVmSnapshotApiPublicBuildVmPublicIdSnapshotPostRaw(requestParameters, initOverrides);
      return await response.value();
    }
    /**
     * Setup SSH key-based authentication for the root user.
     * Setup Root Access
     */
    async setupRootAccessApiPublicBuildVmPublicIdSetupRootAccessPostRaw(requestParameters, initOverrides) {
      if (requestParameters["publicId"] == null) {
        throw new RequiredError(
          "publicId",
          'Required parameter "publicId" was null or undefined when calling setupRootAccessApiPublicBuildVmPublicIdSetupRootAccessPost().'
        );
      }
      if (requestParameters["setupRootPasswordRequest"] == null) {
        throw new RequiredError(
          "setupRootPasswordRequest",
          'Required parameter "setupRootPasswordRequest" was null or undefined when calling setupRootAccessApiPublicBuildVmPublicIdSetupRootAccessPost().'
        );
      }
      const queryParameters = {};
      const headerParameters = {};
      headerParameters["Content-Type"] = "application/json";
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/public-build/vm/{public_id}/setup-root-access`;
      urlPath = urlPath.replace(`{${"public_id"}}`, encodeURIComponent(String(requestParameters["publicId"])));
      const response = await this.request({
        path: urlPath,
        method: "POST",
        headers: headerParameters,
        query: queryParameters,
        body: SetupRootPasswordRequestToJSON(requestParameters["setupRootPasswordRequest"])
      }, initOverrides);
      return new JSONApiResponse(response, (jsonValue) => VMManagementResponseFromJSON(jsonValue));
    }
    /**
     * Setup SSH key-based authentication for the root user.
     * Setup Root Access
     */
    async setupRootAccessApiPublicBuildVmPublicIdSetupRootAccessPost(requestParameters, initOverrides) {
      const response = await this.setupRootAccessApiPublicBuildVmPublicIdSetupRootAccessPostRaw(requestParameters, initOverrides);
      return await response.value();
    }
    /**
     * Setup sandbox development environment with git clone.
     * Setup Sandbox
     */
    async setupSandboxRaw(requestParameters, initOverrides) {
      if (requestParameters["publicId"] == null) {
        throw new RequiredError(
          "publicId",
          'Required parameter "publicId" was null or undefined when calling setupSandbox().'
        );
      }
      if (requestParameters["setupSandboxRequest"] == null) {
        throw new RequiredError(
          "setupSandboxRequest",
          'Required parameter "setupSandboxRequest" was null or undefined when calling setupSandbox().'
        );
      }
      const queryParameters = {};
      const headerParameters = {};
      headerParameters["Content-Type"] = "application/json";
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/public-build/vm/{public_id}/setup-sandbox`;
      urlPath = urlPath.replace(`{${"public_id"}}`, encodeURIComponent(String(requestParameters["publicId"])));
      const response = await this.request({
        path: urlPath,
        method: "POST",
        headers: headerParameters,
        query: queryParameters,
        body: SetupSandboxRequestToJSON(requestParameters["setupSandboxRequest"])
      }, initOverrides);
      return new JSONApiResponse(response, (jsonValue) => SetupSandboxResponseFromJSON(jsonValue));
    }
    /**
     * Setup sandbox development environment with git clone.
     * Setup Sandbox
     */
    async setupSandbox(requestParameters, initOverrides) {
      const response = await this.setupSandboxRaw(requestParameters, initOverrides);
      return await response.value();
    }
    /**
     * Start listeners: write env.py and worker compose from dataset config, then restart worker.
     * Start Worker
     */
    async startWorkerRaw(requestParameters, initOverrides) {
      if (requestParameters["publicId"] == null) {
        throw new RequiredError(
          "publicId",
          'Required parameter "publicId" was null or undefined when calling startWorker().'
        );
      }
      if (requestParameters["vMManagementRequest"] == null) {
        throw new RequiredError(
          "vMManagementRequest",
          'Required parameter "vMManagementRequest" was null or undefined when calling startWorker().'
        );
      }
      const queryParameters = {};
      const headerParameters = {};
      headerParameters["Content-Type"] = "application/json";
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/public-build/vm/{public_id}/start-worker`;
      urlPath = urlPath.replace(`{${"public_id"}}`, encodeURIComponent(String(requestParameters["publicId"])));
      const response = await this.request({
        path: urlPath,
        method: "POST",
        headers: headerParameters,
        query: queryParameters,
        body: VMManagementRequestToJSON(requestParameters["vMManagementRequest"])
      }, initOverrides);
      return new JSONApiResponse(response, (jsonValue) => VMManagementResponseFromJSON(jsonValue));
    }
    /**
     * Start listeners: write env.py and worker compose from dataset config, then restart worker.
     * Start Worker
     */
    async startWorker(requestParameters, initOverrides) {
      const response = await this.startWorkerRaw(requestParameters, initOverrides);
      return await response.value();
    }
  };

  // ../../sdk/typescript-sdk/src/apis/SimulatorApi.ts
  var SimulatorApi = class extends BaseAPI {
    /**
     * Get database configuration from a simulator artifact\'s plato config.  Parses the YAML plato_config and extracts the database listener configuration. The plato_config contains a single dataset configuration (anchors are already resolved). 
     * Get Db Config
     */
    async getSimulatorDbConfigRaw(requestParameters, initOverrides) {
      if (requestParameters["artifactId"] == null) {
        throw new RequiredError(
          "artifactId",
          'Required parameter "artifactId" was null or undefined when calling getSimulatorDbConfig().'
        );
      }
      const queryParameters = {};
      const headerParameters = {};
      if (requestParameters["authorization"] != null) {
        headerParameters["authorization"] = String(requestParameters["authorization"]);
      }
      if (requestParameters["xInternalService"] != null) {
        headerParameters["X-Internal-Service"] = String(requestParameters["xInternalService"]);
      }
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/simulator/{artifact_id}/db_config`;
      urlPath = urlPath.replace(`{${"artifact_id"}}`, encodeURIComponent(String(requestParameters["artifactId"])));
      const response = await this.request({
        path: urlPath,
        method: "GET",
        headers: headerParameters,
        query: queryParameters
      }, initOverrides);
      return new JSONApiResponse(response, (jsonValue) => DbConfigResponseFromJSON(jsonValue));
    }
    /**
     * Get database configuration from a simulator artifact\'s plato config.  Parses the YAML plato_config and extracts the database listener configuration. The plato_config contains a single dataset configuration (anchors are already resolved). 
     * Get Db Config
     */
    async getSimulatorDbConfig(requestParameters, initOverrides) {
      const response = await this.getSimulatorDbConfigRaw(requestParameters, initOverrides);
      return await response.value();
    }
    /**
     * Get Env Flows
     */
    async getSimulatorFlowsRaw(requestParameters, initOverrides) {
      if (requestParameters["artifactId"] == null) {
        throw new RequiredError(
          "artifactId",
          'Required parameter "artifactId" was null or undefined when calling getSimulatorFlows().'
        );
      }
      const queryParameters = {};
      const headerParameters = {};
      if (requestParameters["authorization"] != null) {
        headerParameters["authorization"] = String(requestParameters["authorization"]);
      }
      if (requestParameters["xInternalService"] != null) {
        headerParameters["X-Internal-Service"] = String(requestParameters["xInternalService"]);
      }
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/simulator/{artifact_id}/flows`;
      urlPath = urlPath.replace(`{${"artifact_id"}}`, encodeURIComponent(String(requestParameters["artifactId"])));
      const response = await this.request({
        path: urlPath,
        method: "GET",
        headers: headerParameters,
        query: queryParameters
      }, initOverrides);
      if (this.isJsonMime(response.headers.get("content-type"))) {
        return new JSONApiResponse(response);
      } else {
        return new TextApiResponse(response);
      }
    }
    /**
     * Get Env Flows
     */
    async getSimulatorFlows(requestParameters, initOverrides) {
      const response = await this.getSimulatorFlowsRaw(requestParameters, initOverrides);
      return await response.value();
    }
    /**
     * Get all versions for a specific simulator across all datasets
     * Get Simulator Versions
     */
    async getSimulatorVersionsRaw(requestParameters, initOverrides) {
      if (requestParameters["simulatorName"] == null) {
        throw new RequiredError(
          "simulatorName",
          'Required parameter "simulatorName" was null or undefined when calling getSimulatorVersions().'
        );
      }
      const queryParameters = {};
      if (requestParameters["includeCheckpoints"] != null) {
        queryParameters["include_checkpoints"] = requestParameters["includeCheckpoints"];
      }
      const headerParameters = {};
      if (requestParameters["authorization"] != null) {
        headerParameters["authorization"] = String(requestParameters["authorization"]);
      }
      if (requestParameters["xInternalService"] != null) {
        headerParameters["X-Internal-Service"] = String(requestParameters["xInternalService"]);
      }
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/simulator/{simulator_name}/versions`;
      urlPath = urlPath.replace(`{${"simulator_name"}}`, encodeURIComponent(String(requestParameters["simulatorName"])));
      const response = await this.request({
        path: urlPath,
        method: "GET",
        headers: headerParameters,
        query: queryParameters
      }, initOverrides);
      return new JSONApiResponse(response, (jsonValue) => SimulatorVersionsResponseFromJSON(jsonValue));
    }
    /**
     * Get all versions for a specific simulator across all datasets
     * Get Simulator Versions
     */
    async getSimulatorVersions(requestParameters, initOverrides) {
      const response = await this.getSimulatorVersionsRaw(requestParameters, initOverrides);
      return await response.value();
    }
    /**
     * Get list of all simulators from database
     * List Simulators
     */
    async listSimulatorsRaw(initOverrides) {
      const queryParameters = {};
      const headerParameters = {};
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/simulator/list`;
      const response = await this.request({
        path: urlPath,
        method: "GET",
        headers: headerParameters,
        query: queryParameters
      }, initOverrides);
      return new JSONApiResponse(response, (jsonValue) => jsonValue.map(SimulatorListItemFromJSON));
    }
    /**
     * Get list of all simulators from database
     * List Simulators
     */
    async listSimulators(initOverrides) {
      const response = await this.listSimulatorsRaw(initOverrides);
      return await response.value();
    }
  };

  // ../../sdk/typescript-sdk/src/apis/TestcasesApi.ts
  var TestcasesApi = class extends BaseAPI {
    /**
     * Get Testcases
     */
    async getTestcasesRaw(requestParameters, initOverrides) {
      const queryParameters = {};
      if (requestParameters["startPath"] != null) {
        queryParameters["start_path"] = requestParameters["startPath"];
      }
      if (requestParameters["testCaseSetIds"] != null) {
        queryParameters["test_case_set_ids"] = requestParameters["testCaseSetIds"];
      }
      if (requestParameters["name"] != null) {
        queryParameters["name"] = requestParameters["name"];
      }
      if (requestParameters["prompt"] != null) {
        queryParameters["prompt"] = requestParameters["prompt"];
      }
      if (requestParameters["mode"] != null) {
        queryParameters["mode"] = requestParameters["mode"];
      }
      if (requestParameters["page"] != null) {
        queryParameters["page"] = requestParameters["page"];
      }
      if (requestParameters["pageSize"] != null) {
        queryParameters["page_size"] = requestParameters["pageSize"];
      }
      if (requestParameters["simulatorId"] != null) {
        queryParameters["simulator_id"] = requestParameters["simulatorId"];
      }
      if (requestParameters["simulatorName"] != null) {
        queryParameters["simulator_name"] = requestParameters["simulatorName"];
      }
      if (requestParameters["testCasePublicId"] != null) {
        queryParameters["test_case_public_id"] = requestParameters["testCasePublicId"];
      }
      if (requestParameters["scoringConfigType"] != null) {
        queryParameters["scoring_config_type"] = requestParameters["scoringConfigType"];
      }
      if (requestParameters["isAssigned"] != null) {
        queryParameters["is_assigned"] = requestParameters["isAssigned"];
      }
      if (requestParameters["isSample"] != null) {
        queryParameters["is_sample"] = requestParameters["isSample"];
      }
      if (requestParameters["rejected"] != null) {
        queryParameters["rejected"] = requestParameters["rejected"];
      }
      if (requestParameters["excludeAssignedToAnnotators"] != null) {
        queryParameters["exclude_assigned_to_annotators"] = requestParameters["excludeAssignedToAnnotators"];
      }
      const headerParameters = {};
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/testcases`;
      const response = await this.request({
        path: urlPath,
        method: "GET",
        headers: headerParameters,
        query: queryParameters
      }, initOverrides);
      if (this.isJsonMime(response.headers.get("content-type"))) {
        return new JSONApiResponse(response);
      } else {
        return new TextApiResponse(response);
      }
    }
    /**
     * Get Testcases
     */
    async getTestcases(requestParameters = {}, initOverrides) {
      const response = await this.getTestcasesRaw(requestParameters, initOverrides);
      return await response.value();
    }
  };

  // ../../sdk/typescript-sdk/src/apis/UserApi.ts
  var UserApi = class extends BaseAPI {
    /**
     * Get comprehensive session information for the user\'s organization.  Args:     last_n_hours: Number of hours to look back for peak calculation (default: 1)  Returns:     Dictionary containing:     - running_sessions: Count of currently running sessions     - pending_sessions: Count of sessions that are not ended but have status != RUN_STARTED     - peak_running_count: Peak number of running sessions within the past last_n_hours period 
     * Get Organization Running Sessions Endpoint
     */
    async getOrganizationRunningSessionsEndpointApiUserOrganizationRunningSessionsGetRaw(requestParameters, initOverrides) {
      const queryParameters = {};
      if (requestParameters["lastNHours"] != null) {
        queryParameters["last_n_hours"] = requestParameters["lastNHours"];
      }
      const headerParameters = {};
      if (this.configuration && this.configuration.apiKey) {
        headerParameters["X-Api-Key"] = await this.configuration.apiKey("X-Api-Key");
      }
      let urlPath = `/user/organization/running-sessions`;
      const response = await this.request({
        path: urlPath,
        method: "GET",
        headers: headerParameters,
        query: queryParameters
      }, initOverrides);
      if (this.isJsonMime(response.headers.get("content-type"))) {
        return new JSONApiResponse(response);
      } else {
        return new TextApiResponse(response);
      }
    }
    /**
     * Get comprehensive session information for the user\'s organization.  Args:     last_n_hours: Number of hours to look back for peak calculation (default: 1)  Returns:     Dictionary containing:     - running_sessions: Count of currently running sessions     - pending_sessions: Count of sessions that are not ended but have status != RUN_STARTED     - peak_running_count: Peak number of running sessions within the past last_n_hours period 
     * Get Organization Running Sessions Endpoint
     */
    async getOrganizationRunningSessionsEndpointApiUserOrganizationRunningSessionsGet(requestParameters = {}, initOverrides) {
      const response = await this.getOrganizationRunningSessionsEndpointApiUserOrganizationRunningSessionsGetRaw(requestParameters, initOverrides);
      return await response.value();
    }
  };

  // ../../sdk/typescript-sdk/src/models/GetOperationEventsApiPublicBuildEventsCorrelationIdGet200Response.ts
  var GetOperationEventsApiPublicBuildEventsCorrelationIdGet200ResponseTypeEnum = {
    Connected: "connected",
    Progress: "progress",
    Complete: "complete",
    Error: "error"
  };
  function instanceOfGetOperationEventsApiPublicBuildEventsCorrelationIdGet200Response(value) {
    if (!("type" in value) || value["type"] === void 0) return false;
    return true;
  }
  function GetOperationEventsApiPublicBuildEventsCorrelationIdGet200ResponseFromJSON(json) {
    return GetOperationEventsApiPublicBuildEventsCorrelationIdGet200ResponseFromJSONTyped(json, false);
  }
  function GetOperationEventsApiPublicBuildEventsCorrelationIdGet200ResponseFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "type": json["type"],
      "success": json["success"] == null ? void 0 : json["success"],
      "message": json["message"] == null ? void 0 : json["message"],
      "error": json["error"] == null ? void 0 : json["error"]
    };
  }
  function GetOperationEventsApiPublicBuildEventsCorrelationIdGet200ResponseToJSON(json) {
    return GetOperationEventsApiPublicBuildEventsCorrelationIdGet200ResponseToJSONTyped(json, false);
  }
  function GetOperationEventsApiPublicBuildEventsCorrelationIdGet200ResponseToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "type": value["type"],
      "success": value["success"],
      "message": value["message"],
      "error": value["error"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/MakeEnvResponse.ts
  function instanceOfMakeEnvResponse(value) {
    if (!("jobId" in value) || value["jobId"] === void 0) return false;
    return true;
  }
  function MakeEnvResponseFromJSON(json) {
    return MakeEnvResponseFromJSONTyped(json, false);
  }
  function MakeEnvResponseFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "jobId": json["job_id"],
      "status": json["status"] == null ? void 0 : json["status"]
    };
  }
  function MakeEnvResponseToJSON(json) {
    return MakeEnvResponseToJSONTyped(json, false);
  }
  function MakeEnvResponseToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "job_id": value["jobId"],
      "status": value["status"]
    };
  }

  // ../../sdk/typescript-sdk/src/models/SimulatorStatus.ts
  function instanceOfSimulatorStatus(value) {
    if (!("simulatorName" in value) || value["simulatorName"] === void 0) return false;
    return true;
  }
  function SimulatorStatusFromJSON(json) {
    return SimulatorStatusFromJSONTyped(json, false);
  }
  function SimulatorStatusFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
      return json;
    }
    return {
      "simulatorName": json["simulator_name"],
      "status": json["status"] == null ? void 0 : json["status"]
    };
  }
  function SimulatorStatusToJSON(json) {
    return SimulatorStatusToJSONTyped(json, false);
  }
  function SimulatorStatusToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
      return value;
    }
    return {
      "simulator_name": value["simulatorName"],
      "status": value["status"]
    };
  }

  // sdk-browser-entry.ts
  var OperationTimeoutError = class extends Error {
    constructor(message) {
      super(message);
      this.name = "OperationTimeoutError";
    }
  };
  var OperationFailedError = class extends Error {
    constructor(message) {
      super(message);
      this.name = "OperationFailedError";
    }
  };
  var PlatoClient = class {
    constructor(options) {
      __publicField(this, "env");
      __publicField(this, "publicBuild");
      __publicField(this, "gitea");
      __publicField(this, "simulator");
      __publicField(this, "config");
      __publicField(this, "heartbeatTimers", /* @__PURE__ */ new Map());
      __publicField(this, "heartbeatJobGroupIds", /* @__PURE__ */ new Map());
      __publicField(this, "heartbeatInterval");
      this.heartbeatInterval = options.heartbeatInterval || 3e4;
      this.config = new Configuration({
        basePath: options.basePath || "http://localhost",
        apiKey: options.apiKey
      });
      this.env = new EnvApi(this.config);
      this.publicBuild = new PublicBuildApi(this.config);
      this.gitea = new GiteaApi(this.config);
      this.simulator = new SimulatorApi(this.config);
    }
    async makeEnvironment(request) {
      const response = await this.env.makeEnvironment({ makeEnvRequest2: request });
      if (response.jobId) {
        this.startHeartbeat(response.jobId, response.jobId);
      }
      return response;
    }
    async createSandbox(request) {
      const response = await this.publicBuild.createVM({ createVMRequest: request });
      if (response.correlationId) {
        this.startHeartbeat(response.correlationId, response.correlationId);
      }
      return response;
    }
    async waitForEnvironmentReady(jobGroupId, pollIntervalMs = 2e3, timeoutMs = 3e5) {
      const startTime = Date.now();
      while (true) {
        const status = await this.env.getJobStatus({ jobGroupId });
        if (status.status === "ready") {
          return;
        }
        if (status.status === "failed" || status.status === "error") {
          throw new OperationFailedError(`Environment failed with status: ${status.status}`);
        }
        if (Date.now() - startTime > timeoutMs) {
          throw new OperationTimeoutError(`Environment not ready after ${timeoutMs}ms`);
        }
        await new Promise((resolve) => setTimeout(resolve, pollIntervalMs));
      }
    }
    async closeEnvironment(jobGroupId) {
      this.stopHeartbeat(jobGroupId);
      return await this.env.closeEnvironment({ jobGroupId });
    }
    async closeVM(publicId) {
      this.stopHeartbeat(publicId);
      return await this.publicBuild.closeVM({ publicId });
    }
    startHeartbeat(timerId, jobGroupId) {
      this.stopHeartbeat(timerId);
      this.heartbeatJobGroupIds.set(timerId, jobGroupId);
      const timer = window.setInterval(async () => {
        try {
          await this.env.sendHeartbeat({ jobId: jobGroupId });
        } catch (error) {
          console.error(`Heartbeat failed for ${jobGroupId}:`, error);
        }
      }, this.heartbeatInterval);
      this.heartbeatTimers.set(timerId, timer);
    }
    stopHeartbeat(timerId) {
      const timer = this.heartbeatTimers.get(timerId);
      if (timer) {
        window.clearInterval(timer);
        this.heartbeatTimers.delete(timerId);
        this.heartbeatJobGroupIds.delete(timerId);
      }
    }
    stopAllHeartbeats() {
      for (const timer of this.heartbeatTimers.values()) {
        window.clearInterval(timer);
      }
      this.heartbeatTimers.clear();
      this.heartbeatJobGroupIds.clear();
    }
    destroy() {
      this.stopAllHeartbeats();
    }
  };
  return __toCommonJS(sdk_browser_entry_exports);
})();
//# sourceMappingURL=plato-sdk-bundle.js.map

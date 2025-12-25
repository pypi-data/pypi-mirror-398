// Browser-compatible entry point for Plato SDK
// Excludes Node.js-only modules like flow/executor

// Re-export runtime
export * from '../../sdk/typescript-sdk/src/runtime';

// Re-export all APIs
export * from '../../sdk/typescript-sdk/src/apis/EnvApi';
export * from '../../sdk/typescript-sdk/src/apis/GiteaApi';
export * from '../../sdk/typescript-sdk/src/apis/PublicBuildApi';
export * from '../../sdk/typescript-sdk/src/apis/SimulatorApi';
export * from '../../sdk/typescript-sdk/src/apis/TestcasesApi';
export * from '../../sdk/typescript-sdk/src/apis/UserApi';

// Re-export all models
export * from '../../sdk/typescript-sdk/src/models/Authentication';
export * from '../../sdk/typescript-sdk/src/models/BaseScoringConfig';
export * from '../../sdk/typescript-sdk/src/models/BaseStructuredRunLog';
export * from '../../sdk/typescript-sdk/src/models/BatchLogRequest';
export * from '../../sdk/typescript-sdk/src/models/ChromeCookie';
export * from '../../sdk/typescript-sdk/src/models/CreateSimulatorRequest';
export * from '../../sdk/typescript-sdk/src/models/CreateSnapshotRequest';
export * from '../../sdk/typescript-sdk/src/models/CreateSnapshotResponse';
export * from '../../sdk/typescript-sdk/src/models/CreateVMRequest';
export * from '../../sdk/typescript-sdk/src/models/CreateVMResponse';
export * from '../../sdk/typescript-sdk/src/models/DbConfigResponse';
export * from '../../sdk/typescript-sdk/src/models/EvaluateRequest';
export * from '../../sdk/typescript-sdk/src/models/GetOperationEvents200Response';
export * from '../../sdk/typescript-sdk/src/models/GetOperationEventsApiPublicBuildEventsCorrelationIdGet200Response';
export * from '../../sdk/typescript-sdk/src/models/HTTPValidationError';
export * from '../../sdk/typescript-sdk/src/models/JobStatusResponse';
export * from '../../sdk/typescript-sdk/src/models/LocationInner';
export * from '../../sdk/typescript-sdk/src/models/Log';
export * from '../../sdk/typescript-sdk/src/models/MakeEnvRequest2';
export * from '../../sdk/typescript-sdk/src/models/MakeEnvResponse';
export * from '../../sdk/typescript-sdk/src/models/ResetEnvRequest';
export * from '../../sdk/typescript-sdk/src/models/ResetEnvTask';
export * from '../../sdk/typescript-sdk/src/models/ScoreRequest';
export * from '../../sdk/typescript-sdk/src/models/SetupRootPasswordRequest';
export * from '../../sdk/typescript-sdk/src/models/SetupSandboxRequest';
export * from '../../sdk/typescript-sdk/src/models/SetupSandboxResponse';
export * from '../../sdk/typescript-sdk/src/models/SimConfigCompute';
export * from '../../sdk/typescript-sdk/src/models/SimConfigDataset';
export * from '../../sdk/typescript-sdk/src/models/SimConfigListener';
export * from '../../sdk/typescript-sdk/src/models/SimConfigMetadata';
export * from '../../sdk/typescript-sdk/src/models/SimConfigService';
export * from '../../sdk/typescript-sdk/src/models/SimStatusHistory';
export * from '../../sdk/typescript-sdk/src/models/SimulatorConfig';
export * from '../../sdk/typescript-sdk/src/models/SimulatorListItem';
export * from '../../sdk/typescript-sdk/src/models/SimulatorStatus';
export * from '../../sdk/typescript-sdk/src/models/SimulatorVersionDetails';
export * from '../../sdk/typescript-sdk/src/models/SimulatorVersionsResponse';
export * from '../../sdk/typescript-sdk/src/models/ValidationError';
export * from '../../sdk/typescript-sdk/src/models/VMManagementRequest';
export * from '../../sdk/typescript-sdk/src/models/VMManagementResponse';
export * from '../../sdk/typescript-sdk/src/models/WorkerReadyResponse';

// Browser-compatible PlatoClient (copy of original without flow module dependency)
import { Configuration } from '../../sdk/typescript-sdk/src/runtime';
import {
    EnvApi,
    PublicBuildApi,
    GiteaApi,
    SimulatorApi,
} from '../../sdk/typescript-sdk/src/apis/index';

import type {
    MakeEnvRequest2,
    CreateVMRequest,
    CreateVMResponse,
} from '../../sdk/typescript-sdk/src/models/index';

export interface PlatoClientOptions {
    apiKey: string;
    basePath?: string;
    heartbeatInterval?: number;
}

export interface OperationEvent {
    type: string;
    success?: boolean;
    message?: string;
    error?: string;
}

export class OperationTimeoutError extends Error {
    constructor(message: string) {
        super(message);
        this.name = 'OperationTimeoutError';
    }
}

export class OperationFailedError extends Error {
    constructor(message: string) {
        super(message);
        this.name = 'OperationFailedError';
    }
}

export class PlatoClient {
    public readonly env: EnvApi;
    public readonly publicBuild: PublicBuildApi;
    public readonly gitea: GiteaApi;
    public readonly simulator: SimulatorApi;

    private readonly config: Configuration;
    private readonly heartbeatTimers: Map<string, number> = new Map();
    private readonly heartbeatJobGroupIds: Map<string, string> = new Map();
    private readonly heartbeatInterval: number;

    constructor(options: PlatoClientOptions) {
        this.heartbeatInterval = options.heartbeatInterval || 30000;

        this.config = new Configuration({
            basePath: options.basePath || 'http://localhost',
            apiKey: options.apiKey,
        });

        this.env = new EnvApi(this.config);
        this.publicBuild = new PublicBuildApi(this.config);
        this.gitea = new GiteaApi(this.config);
        this.simulator = new SimulatorApi(this.config);
    }

    async makeEnvironment(request: MakeEnvRequest2): Promise<{ [key: string]: any; }> {
        const response = await this.env.makeEnvironment({ makeEnvRequest2: request });
        
        if ((response as any).jobId) {
            this.startHeartbeat((response as any).jobId, (response as any).jobId);
        }

        return response;
    }

    async createSandbox(request: CreateVMRequest): Promise<CreateVMResponse> {
        const response = await this.publicBuild.createVM({ createVMRequest: request });
        
        if (response.correlationId) {
            this.startHeartbeat(response.correlationId, response.correlationId);
        }

        return response;
    }

    async waitForEnvironmentReady(
        jobGroupId: string,
        pollIntervalMs: number = 2000,
        timeoutMs: number = 300000
    ): Promise<void> {
        const startTime = Date.now();
        
        while (true) {
            const status = await this.env.getJobStatus({ jobGroupId });
            
            if (status.status === 'ready') {
                return;
            }
            
            if (status.status === 'failed' || status.status === 'error') {
                throw new OperationFailedError(`Environment failed with status: ${status.status}`);
            }
            
            if (Date.now() - startTime > timeoutMs) {
                throw new OperationTimeoutError(`Environment not ready after ${timeoutMs}ms`);
            }
            
            await new Promise(resolve => setTimeout(resolve, pollIntervalMs));
        }
    }

    async closeEnvironment(jobGroupId: string): Promise<any> {
        this.stopHeartbeat(jobGroupId);
        return await this.env.closeEnvironment({ jobGroupId });
    }

    async closeVM(publicId: string): Promise<any> {
        this.stopHeartbeat(publicId);
        return await this.publicBuild.closeVM({ publicId });
    }

    private startHeartbeat(timerId: string, jobGroupId: string): void {
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

    private stopHeartbeat(timerId: string): void {
        const timer = this.heartbeatTimers.get(timerId);
        if (timer) {
            window.clearInterval(timer);
            this.heartbeatTimers.delete(timerId);
            this.heartbeatJobGroupIds.delete(timerId);
        }
    }

    stopAllHeartbeats(): void {
        for (const timer of this.heartbeatTimers.values()) {
            window.clearInterval(timer);
        }
        this.heartbeatTimers.clear();
        this.heartbeatJobGroupIds.clear();
    }

    destroy(): void {
        this.stopAllHeartbeats();
    }
}

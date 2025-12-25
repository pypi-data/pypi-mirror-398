// Real Plato API Client using bundled SDK from sdk/typescript-sdk
class PlatoApiClient {
  constructor(apiKey) {
    this.apiKey = apiKey;
    this.baseUrl = 'https://plato.so/api';
    this.client = null;
  }

  init() {
    if (!window.PlatoSDK) {
      throw new Error('Plato SDK not loaded');
    }

    // Create PlatoClient - handles heartbeats automatically
    this.client = new window.PlatoSDK.PlatoClient({
      apiKey: this.apiKey,
      basePath: this.baseUrl,
    });

    this.currentJobId = null;
  }

  /**
   * Create environment and return session object
   */
  async createEnvironment(simulatorName, artifactId = null) {
    if (!this.client) this.init();

    // Call SDK makeEnvironment via PlatoClient (handles heartbeats automatically)
    const response = await this.client.makeEnvironment({
      envId: simulatorName,
      interfaceType: 'browser',
      interfaceWidth: 1280,
      interfaceHeight: 720,
      source: 'SDK',
      openPageOnStart: false,
      envConfig: {},
      recordActions: false,
      keepalive: false,
      fast: false,
      artifactId: artifactId || undefined,
    });

    const jobId = response.jobId || response.job_id;
    const alias = response.alias;

    if (!jobId) {
      throw new Error('No job ID returned from makeEnvironment');
    }

    // Store jobId for cleanup later
    this.currentJobId = jobId;

    // Wait for ready
    await this.waitForReady(jobId, 120000);

    // Get the actual public URL
    const environmentUrl = this.getPublicUrl(alias || jobId);

    return {
      environmentId: jobId,
      environmentUrl: environmentUrl,
      alias: alias,
    };
  }

  /**
   * Wait for environment to be ready
   */
  async waitForReady(jobId, timeout = 120000) {
    const startTime = Date.now();
    let baseDelay = 500;
    const maxDelay = 8000;

    // Wait for the job to be running
    let currentDelay = baseDelay;
    while (true) {
      const status = await this.client.env.getJobStatus({ jobGroupId: jobId });
      if (status.status && status.status.toLowerCase() === 'running') {
        break;
      }

      // Add jitter
      const jitter = (Math.random() - 0.5) * 0.5 * currentDelay;
      await new Promise(resolve => setTimeout(resolve, currentDelay + jitter));

      if (Date.now() - startTime > timeout) {
        throw new Error('Environment failed to start - job never entered running state');
      }

      currentDelay = Math.min(currentDelay * 2, maxDelay);
    }

    // Wait for the worker to be ready and healthy
    currentDelay = baseDelay;
    while (true) {
      const workerStatus = await this.client.env.getWorkerReadyApiEnvJobIdWorkerReadyGet({ jobId: jobId });
      if (workerStatus.ready) {
        break;
      }

      const jitter = (Math.random() - 0.5) * 0.5 * currentDelay;
      await new Promise(resolve => setTimeout(resolve, currentDelay + jitter));

      if (Date.now() - startTime > timeout) {
        const errorMsg = workerStatus.error || 'Unknown error';
        throw new Error(`Environment failed to start - worker not ready: ${errorMsg}`);
      }

      currentDelay = Math.min(currentDelay * 2, maxDelay);
    }
  }

  /**
   * Close environment and stop heartbeats
   */
  async closeEnvironment(jobId = null) {
    const id = jobId || this.currentJobId;
    if (!id) {
      console.warn('No environment to close');
      return;
    }

    try {
      await this.client.closeEnvironment(id);
    } catch (error) {
      console.error('Error closing environment:', error);
    }

    this.currentJobId = null;
  }

  /**
   * Stop all heartbeats (call when extension is done)
   */
  destroy() {
    if (this.client) {
      this.client.destroy();
    }
    this.currentJobId = null;
  }

  /**
   * Get the public URL for accessing an environment
   */
  getPublicUrl(identifier) {
    // Determine environment based on base_url
    if (this.baseUrl.includes('localhost:8080')) {
      return `http://localhost:8081/${identifier}`;
    } else if (this.baseUrl.includes('dev.plato.so')) {
      return `https://${identifier}.dev.sims.plato.so`;
    } else if (this.baseUrl.includes('staging.plato.so')) {
      return `https://${identifier}.staging.sims.plato.so`;
    } else if (this.baseUrl.includes('plato.so') && !this.baseUrl.includes('staging') && !this.baseUrl.includes('dev')) {
      return `https://${identifier}.sims.plato.so`;
    } else {
      throw new Error('Unknown base URL: ' + this.baseUrl);
    }
  }

  /**
   * Get simulator info
   */
  async getSimulator(simulatorName) {
    const response = await fetch(`${this.baseUrl}/simulator/${simulatorName}`, {
      headers: { 'X-API-Key': this.apiKey }
    });

    if (!response.ok) {
      throw new Error(`Simulator not found: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Submit review
   */
  async submitReview(simulatorName, review) {
    // Get simulator info
    const simulator = await this.getSimulator(simulatorName);
    const simulatorId = simulator.id;
    const currentConfig = simulator.config || {};
    const existingReviews = currentConfig.reviews || [];
    const currentStatus = currentConfig.status || 'not_started';

    if (currentStatus != 'data_review_requested') {
      throw new Error(
        `Cannot submit review: Simulator is in wrong state "${currentStatus}". ` +
        `Must be in a data review state: data_review_requested`
      );
    }

    let newStatus;

    if (review.outcome === 'pass') {
      newStatus = 'ready';
    } else if (review.outcome === 'reject') {
      newStatus = 'data_in_progress';
    } else {
      return { success: true, message: 'Skipped' };
    }


    // Extract video and events paths from recordings array (should only have one recording)
    const recording = review.recordings && review.recordings.length > 0 ? review.recordings[0] : null;
    if (!recording || !recording.video_s3_path || !recording.events_s3_path) {
      throw new Error('Recording paths are required for review submission');
    }

    // Build review object matching SimReview model
    const reviewObject = {
      review_type: 'data', // Environment recording reviews are always 'env'
      outcome: review.outcome,
      artifact_id: review.artifactId,
      video_s3_path: recording.video_s3_path,
      events_s3_path: recording.events_s3_path,
      comments: review.comments || null,
      timestamp_iso: new Date().toISOString()
    };

    // Submit
    const response = await fetch(`${this.baseUrl}/env/simulators/${simulatorId}`, {
      method: 'PUT',
      headers: {
        'X-API-Key': this.apiKey,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        config: {
          ...currentConfig,
          status: newStatus,
          reviews: [...existingReviews, reviewObject]
        }
      })
    });

    if (!response.ok) {
      const errorText = await response.text().catch(() => response.statusText);
      throw new Error(`Failed to submit review: ${errorText}`);
    }

    return { success: true, newStatus };
  }

  /**
   * Tag artifact as prod-latest
   */
  async tagArtifact(simulatorName, artifactId) {
    const response = await fetch(`${this.baseUrl}/simulator/update-tag`, {
      method: 'POST',
      headers: {
        'X-API-Key': this.apiKey,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        simulator_name: simulatorName,
        artifact_id: artifactId,
        tag_name: 'prod-latest',
        dataset: 'base'
      })
    });

    if (!response.ok) {
      throw new Error(`Failed to tag artifact: ${response.statusText}`);
    }

    return await response.json();
  }
}

window.PlatoApiClient = PlatoApiClient;

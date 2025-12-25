import * as timers from 'node:timers/promises';
import { SSMClient, GetParameterCommand } from '@aws-sdk/client-ssm';
import axios, { AxiosInstance } from 'axios';
import { Config } from '../config.js';

type HealthStatus = 'HEALTHY' | 'WARNING' | 'CRITICAL';

interface HeartbeatOptions {
	signal: AbortSignal;
	interval: number;
}

/**
 * Health monitoring service that reports status to TDP platform
 * Only runs in production mode
 */
export class HealthService {
	private config: Config;
	private authToken: string | null = null;
	private ssmClient: SSMClient;
	private httpClient: AxiosInstance;
	private consecutiveFailures = 0;
	private isRunning = false;
	private heartbeatController?: AbortController;

	constructor(config: Config) {
		this.config = config;
		this.ssmClient = new SSMClient({ region: config.awsRegion });
		this.httpClient = axios.create({
			timeout: 30000,
			headers: {
				Accept: 'application/json',
				'Content-Type': 'application/json',
			},
		});
	}

	private async getToken(): Promise<string> {
		if (this.authToken) {
			return this.authToken;
		}

		// Allow overwriting the token with an environment variable (for local dev)
		const envToken = process.env.TDP_TOKEN;
		if (envToken) {
			this.authToken = envToken;
			return this.authToken;
		}

		try {
			const command = new GetParameterCommand({
				Name: this.config.jwtTokenParameter,
				WithDecryption: true,
			});

			const response = await this.ssmClient.send(command);
			if (!response.Parameter?.Value) {
				throw new Error('No token value returned from SSM');
			}

			this.authToken = response.Parameter.Value;
			return this.authToken;
		} catch (error) {
			console.error('Failed to retrieve token from SSM:', error);
			throw error;
		}
	}

	private async makeAuthenticatedRequest(
		method: 'GET' | 'POST' | 'PUT',
		url: string,
		data?: unknown,
	): Promise<unknown> {
		const token = await this.getToken();
		const headers = {
			'ts-auth-token': token,
			'x-org-slug': this.config.orgSlug,
		};

		try {
			const response = await this.httpClient.request({
				method,
				url,
				headers,
				data,
			});
			return response.data;
		} catch (error) {
			console.error(`HTTP ${method} request failed:`, { url, error });
			throw error;
		}
	}

	async heartbeat(): Promise<void> {
		if (!this.config.connectorId) {
			console.warn('No connector ID found, skipping heartbeat');
			return;
		}

		const url = `${this.config.tdpEndpoint}/v1/data-acquisition/connectors/${this.config.connectorId}/heartbeat`;

		try {
			await this.makeAuthenticatedRequest('POST', url);
			console.log('Heartbeat sent', { connectorId: this.config.connectorId });
		} catch (error) {
			console.warn('Failed to send heartbeat:', error);
			throw error;
		}
	}

	async reportHealth(status: HealthStatus, errorCode?: string): Promise<void> {
		if (!this.config.connectorId) {
			console.warn('No connector ID found, skipping health report');
			return;
		}

		const url = `${this.config.tdpEndpoint}/v1/data-acquisition/connectors/${this.config.connectorId}/health`;
		const data: { status: HealthStatus; errorCode?: string } = { status };

		if (errorCode) {
			data.errorCode = errorCode;
		}

		try {
			await this.makeAuthenticatedRequest('PUT', url, data);
			console.log('Health reported', {
				connectorId: this.config.connectorId,
				status,
			});
		} catch (error) {
			console.warn('Failed to report health:', error);
			throw error;
		}
	}

	startHeartbeat(options: HeartbeatOptions): void {
		if (this.isRunning) {
			return;
		}

		this.isRunning = true;
		this.heartbeatController = new AbortController();

		this.runHeartbeat({
			signal: this.heartbeatController.signal,
			interval: options.interval,
		});
	}

	stopHeartbeat(): void {
		this.isRunning = false;
		if (this.heartbeatController) {
			this.heartbeatController.abort();
		}
		console.log('Heartbeat monitoring stopped');
	}

	private async runHeartbeat(options: HeartbeatOptions): Promise<void> {
		while (!options.signal.aborted && this.isRunning) {
			try {
				await this.heartbeat();
				await this.reportHealth('HEALTHY');
				this.consecutiveFailures = 0;
			} catch (error) {
				this.consecutiveFailures++;
				if (
					this.consecutiveFailures >= 5 &&
					this.consecutiveFailures % 5 === 0
				) {
					console.error('Heartbeat is failing repeatedly', {
						error,
						consecutiveFailures: this.consecutiveFailures,
					});
				}
			}

			try {
				await timers.setTimeout(options.interval, undefined, {
					signal: options.signal,
				});
			} catch {
				// Timeout was aborted, exit loop
				break;
			}
		}

		console.log('Heartbeat loop ended');
	}
}

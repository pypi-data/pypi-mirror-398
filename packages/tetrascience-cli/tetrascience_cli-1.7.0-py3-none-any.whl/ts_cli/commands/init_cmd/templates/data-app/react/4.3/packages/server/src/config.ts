/**
 * Server configuration from environment variables
 */
export class Config {
	// TDP connection settings
	readonly tdpEndpoint: string;
	readonly orgSlug: string;
	readonly tsAuthToken: string; // Comes from cookies in production, .env.server in local dev

	// Server settings
	readonly port: number;
	readonly isProduction: boolean;

	// Healthcheck settings (only used when enabled)
	readonly awsRegion: string;
	readonly connectorId: string | undefined;
	readonly jwtTokenParameter: string;
	readonly healthCheckInterval: number;
	readonly enableHealthcheck: boolean;

	constructor() {
		// Server settings
		this.port = parseInt(process.env.PORT || '3000');
		this.isProduction = process.env.NODE_ENV === 'production';

		// Healthcheck is enabled when ENABLE_HEALTHCHECK=true (set in production supervisord.conf)
		this.enableHealthcheck = process.env.ENABLE_HEALTHCHECK === 'true';

		// TDP connection settings
		this.tdpEndpoint = process.env.TDP_ENDPOINT || '';
		this.orgSlug = process.env.ORG_SLUG || '';
		this.tsAuthToken = process.env.TS_AUTH_TOKEN || '';

		// Healthcheck settings (required only when healthcheck is enabled)
		this.awsRegion = process.env.AWS_REGION || '';
		this.connectorId = process.env.CONNECTOR_ID;
		this.jwtTokenParameter = process.env.JWT_TOKEN_PARAMETER || '';
		this.healthCheckInterval = parseInt(
			process.env.HEALTH_CHECK_INTERVAL_MS || '60000',
		);

		// Validate required config
		if (!this.tdpEndpoint) {
			console.warn('TDP_ENDPOINT is not set - TDP API calls will fail');
		}
		if (!this.orgSlug) {
			console.warn('ORG_SLUG is not set - TDP API calls will fail');
		}
	}
}

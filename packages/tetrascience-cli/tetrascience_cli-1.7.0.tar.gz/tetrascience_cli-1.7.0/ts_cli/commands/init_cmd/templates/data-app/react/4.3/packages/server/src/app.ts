import express, { Express, Request, Response, NextFunction } from 'express';
import cookieParser from 'cookie-parser';
import ViteExpress from 'vite-express';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { createServer } from 'net';
import { Config } from './config.js';
import { HealthService } from './services/health-service.js';

/**
 * Check if a port is available
 */
function checkPortAvailable(port: number): Promise<void> {
	return new Promise((resolve, reject) => {
		const server = createServer();
		server.once('error', (err: NodeJS.ErrnoException) => {
			if (err.code === 'EADDRINUSE') {
				reject(
					new Error(
						`Port ${port} is already in use. Please free the port or use a different one.`,
					),
				);
			} else {
				reject(err);
			}
		});
		server.once('listening', () => {
			server.close(() => resolve());
		});
		server.listen(port);
	});
}

// Extend Express Request type to include tdpAuth
interface RequestWithAuth extends Request {
	tdpAuth?: {
		token: string;
		orgSlug: string;
	};
}

export class ExpressAppServer {
	private _app: Express | undefined;
	private _server: ReturnType<typeof ViteExpress.listen> | undefined;
	private healthService?: HealthService;
	private healthAbortController?: AbortController;
	readonly config: Config;

	constructor(config?: Config) {
		this.config = config || new Config();
	}

	async init() {
		this._app = express();

		// Middleware
		this.app.use(express.json());
		this.app.use(cookieParser());

		// Add no-cache headers to prevent auth issues from cached responses
		this.app.use((_req: Request, res: Response, next: NextFunction) => {
			res.setHeader(
				'Cache-Control',
				'no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0',
			);
			res.setHeader('Pragma', 'no-cache');
			res.setHeader('Expires', '0');
			next();
		});

		// Add auth headers from cookies or config
		this.app.use((req: Request, _res: Response, next: NextFunction) => {
			// Get auth from cookies (production) or config (local dev)
			const token = req.cookies['ts-auth-token'] || this.config.tsAuthToken;
			const orgSlug = req.cookies['x-org-slug'] || this.config.orgSlug;

			// Attach to request for use in routes
			(req as RequestWithAuth).tdpAuth = { token, orgSlug };
			next();
		});

		// API Routes
		this.registerRoutes();

		// Error handler
		this.app.use(
			(err: Error, _req: Request, res: Response, _next: NextFunction) => {
				console.error('Server error:', err);
				res.status(500).json({ error: err.message });
			},
		);

		// Initialize health monitoring when enabled (production deployments)
		if (this.config.enableHealthcheck) {
			await this.initHealthMonitoring();
		}
	}

	/**
	 * Register API routes - add your custom endpoints here!
	 *
	 * Examples included:
	 * - GET /api/health - Health check endpoint
	 * - GET /api/hello - Simple hello world example
	 * - GET /api/user - Example showing auth context usage
	 * - POST /api/data - Example POST endpoint
	 */
	private registerRoutes() {
		// Health check endpoint (for load balancers, etc.)
		this.app.get('/api/health', (_req: Request, res: Response) => {
			res.json({ status: 'ok', timestamp: new Date().toISOString() });
		});

		// ============================================
		// SAMPLE ENDPOINTS - Modify or remove as needed
		// ============================================

		// Simple GET endpoint
		this.app.get('/api/hello', (_req: Request, res: Response) => {
			res.json({ message: 'Hello from Express server!' });
		});

		// GET endpoint demonstrating auth context
		this.app.get('/api/user', (req: Request, res: Response) => {
			const auth = (req as RequestWithAuth).tdpAuth;
			res.json({
				message: 'User info endpoint',
				orgSlug: auth?.orgSlug || 'not authenticated',
				hasToken: !!auth?.token,
			});
		});

		// POST endpoint example
		this.app.post('/api/data', (req: Request, res: Response) => {
			const { data } = req.body;
			res.json({
				message: 'Data received successfully',
				receivedData: data,
				timestamp: new Date().toISOString(),
			});
		});

		// ============================================
		// ADD YOUR CUSTOM ENDPOINTS BELOW
		// ============================================

		// Example: this.app.get("/api/my-endpoint", (req, res) => { ... });
	}

	private async initHealthMonitoring(): Promise<void> {
		const hasSsmConfig = this.config.awsRegion && this.config.jwtTokenParameter;
		const hasDirectToken = !!process.env.TDP_TOKEN;

		if (!hasSsmConfig && !hasDirectToken) {
			console.error(
				'Healthcheck not configured. Set JWT_TOKEN_PARAMETER + AWS_REGION, or TDP_TOKEN',
			);
			return;
		}

		try {
			this.healthService = new HealthService(this.config);

			// Report initial health status
			await this.healthService.reportHealth('HEALTHY');

			// Start heartbeat monitoring
			this.healthAbortController = new AbortController();
			this.healthService.startHeartbeat({
				signal: this.healthAbortController.signal,
				interval: this.config.healthCheckInterval,
			});

			console.log('Health monitoring initialized successfully');
		} catch (error) {
			console.error('Failed to initialize health monitoring:', error);
		}
	}

	get app(): Express {
		if (this._app === undefined) {
			throw new Error('Express server is not initialized');
		}
		return this._app;
	}

	async start() {
		if (this.app === undefined) {
			throw new Error('Express server is not initialized');
		}

		// Check if port is available before starting
		await checkPortAvailable(this.config.port);

		// Configure ViteExpress to use the client package
		const __filename = fileURLToPath(import.meta.url);
		const __dirname = dirname(__filename);
		const clientRoot = resolve(__dirname, '../../client');

		ViteExpress.config({
			mode: this.config.isProduction ? 'production' : 'development',
			viteConfigFile: resolve(clientRoot, 'vite.config.ts'),
			inlineViteConfig: {
				root: clientRoot,
				build: {
					outDir: resolve(clientRoot, 'dist'),
				},
			},
		});

		this._server = ViteExpress.listen(this.app, this.config.port, () =>
			console.log(`Server is listening on port ${this.config.port}...`),
		);
	}

	close() {
		// Stop health monitoring if running
		if (this.healthAbortController) {
			console.log('Stopping health monitoring...');
			this.healthAbortController.abort();
			this.healthService?.stopHeartbeat();
		}

		if (this._server) {
			this._server.close();
			console.log('Server closed');
		}
	}
}

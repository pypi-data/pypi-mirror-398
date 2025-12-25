import { ExpressAppServer } from './app.js';
import { Config } from './config.js';

const main = async () => {
	const config = new Config();
	const server = new ExpressAppServer(config);

	// Initialize and start the server
	await server.init();
	await server.start();

	// Handle graceful shutdown
	const handleShutdown = (signal: string) => {
		console.log(`Received ${signal}, shutting down gracefully...`);
		server.close();
		process.exit(0);
	};

	process.on('SIGTERM', () => handleShutdown('SIGTERM'));
	process.on('SIGINT', () => handleShutdown('SIGINT'));
};

main().catch((error) => {
	console.error('Failed to start server:', error);
	process.exit(1);
});

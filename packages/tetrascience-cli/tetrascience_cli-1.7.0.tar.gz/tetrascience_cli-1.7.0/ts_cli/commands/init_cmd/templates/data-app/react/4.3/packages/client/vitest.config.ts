/// <reference types="@vitest/browser/providers/playwright" />
import { defineConfig } from 'vitest/config'
import viteDefaultConfig from './vite.config'

export default defineConfig({

    test: {
        coverage: {
            provider: 'v8'
        },
        workspace: [
            {
                ...viteDefaultConfig,
                test: {
                    // an example of file based convention,
                    // you don't have to follow it
                    include: [
                        'tests/unit/**/*.{test,spec}.{ts,tsx}',
                        'tests/**/*.unit.{test,spec}.{ts,tsx}',
                    ],
                    name: 'unit',
                    environment: 'node',

                },
            },
            {
                ...viteDefaultConfig,
                test: {
                    // an example of file based convention,
                    // you don't have to follow it
                    include: [
                        'tests/browser/**/*.{test,spec}.{ts,tsx}',
                        'tests/**/*.browser.{test,spec}.{ts,tsx}',
                    ],
                    name: 'browser',
                    browser: {
                        provider: 'playwright',
                        enabled: true,
                        headless: true,
                        instances: [
                            { browser: 'chromium' },
                        ],
                        screenshotFailures: true,
                    },
                },
            },
        ],
    },
})
import { BenchmarkRunner } from './benchmark-runner.js';
import http from 'k6/http';
import { check } from 'k6';

export class WaitWrite extends BenchmarkRunner {
    static run(baseUrl, requestParams, benchmarkGraphOptions) {
        let url = `${baseUrl}/runs/wait`;

        // Create a payload with the LangGraph agent configuration
        const payload = JSON.stringify({
            assistant_id: benchmarkGraphOptions.graph_id,
            input: benchmarkGraphOptions.input,
            config: {
                recursion_limit: benchmarkGraphOptions.input.expand + 2,
            },
        });

        // If the request is stateful, create a thread first and use it in the url
        if (benchmarkGraphOptions.stateful) {
            const thread = http.post(`${baseUrl}/threads`, "{}", requestParams);
            const threadId = thread.json().thread_id;
            url = `${baseUrl}/threads/${threadId}/runs/wait`;
        }

        // Make a single request to the wait endpoint
        const result = http.post(url, payload, requestParams);

        return result;
    }

    static validate(result, errorMetrics, benchmarkGraphOptions) {
        const expected_length = benchmarkGraphOptions.input.mode === 'single' ? 1 : benchmarkGraphOptions.input.expand + 1;
        let success = false;
        try {
            success = check(result, {
                'Run completed successfully': (r) => r.status === 200,
                'Response contains expected number of messages': (r) => r.json().messages?.length === expected_length,
            });
        } catch (error) {
            console.log(`Unknown error checking result: ${error.message}`);
        }

        if (!success) {
            // Classify error based on status code or response
            if (result.status >= 500) {
                errorMetrics.server_errors.add(1);
                console.log(`Server error: ${result.status}`);
            } else if (result.status === 408 || result.error?.includes('timeout')) {
                errorMetrics.timeout_errors.add(1);
                console.log(`Timeout error: ${result.error}`);
            } else if (result.status === 200 && result.json().messages?.length !== expected_length) {
                errorMetrics.missing_message_errors.add(1);
                console.log(`Missing message error: Status ${result.status}, ${JSON.stringify(result.body)}, ${result.headers?.['Content-Location']}`);
            } else {
                errorMetrics.other_errors.add(1);
                console.log(`Other error: Status ${result.status}, ${JSON.stringify(result.body)}`);
            }
        }
        return success;
    }

    static toString() {
        return 'wait_write';
    }
}
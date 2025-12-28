/*
 * Delete all threads and runs from the last benchmark run for consistent tests
 * The default benchmark server has a thread TTL of one hour that should clean things up too so this doesn't run too long.
 */

// URL of your Agent Server
const BASE_URL = process.env.BASE_URL || 'http://localhost:9123';
// LangSmith API key only needed with a custom server endpoint
const LANGSMITH_API_KEY = process.env.LANGSMITH_API_KEY;

async function clean() {
    try {
        await cleanAssistants();
        await cleanThreads();
    } catch (error) {
        console.error('Fatal error during cleanup:', error.message);
        process.exit(1);
    }
}

async function cleanAssistants() {
    const headers = { 'Content-Type': 'application/json' };
    if (LANGSMITH_API_KEY) {
        headers['x-api-key'] = LANGSMITH_API_KEY;
    }

    const searchUrl = `${BASE_URL}/assistants/search`;
    let totalDeleted = 0;

    console.log('Starting assistant cleanup...');

    while (true) {
        // Get the next page of assistants
        console.log('Searching for assistants...');
        const searchResponse = await fetch(searchUrl, {
            method: 'POST',
            headers,
            body: JSON.stringify({
                limit: 1000,
                metadata: {
                    created_by: 'benchmark' // NOTE: Super important to not clean up the assistants created by the system
                }
             })
        });

        if (!searchResponse.ok) {
            throw new Error(`Search request failed: ${searchResponse.status} ${searchResponse.statusText}`);
        }

        const assistants = await searchResponse.json();

        // If no assistants found, we're done
        if (!assistants || assistants.length === 0) {
            console.log('No more assistants found.');
            break;
        }

        console.log(`Found ${assistants.length} assistants to delete`);

        // Delete each assistant
        for (const assistant of assistants) {
            try {
                const deleteUrl = `${BASE_URL}/assistants/${assistant.assistant_id}`;
                const deleteResponse = await fetch(deleteUrl, {
                    method: 'DELETE',
                    headers
                });

                if (!deleteResponse.ok) {
                    console.error(`Failed to delete assistant ${assistant.assistant_id}: ${deleteResponse.status} ${deleteResponse.statusText}`);
                } else {
                    totalDeleted++;
                }
            } catch (deleteError) {
                console.error(`Error deleting assistant ${assistant.assistant_id}:`, deleteError.message);
            }
        }

        console.log(`Deleted ${assistants.length} assistants in this batch`);
    }

    console.log(`Assistant cleanup completed. Total assistants deleted: ${totalDeleted}`);
}


async function cleanThreads() {
    const headers = { 'Content-Type': 'application/json' };
    if (LANGSMITH_API_KEY) {
        headers['x-api-key'] = LANGSMITH_API_KEY;
    }

    const searchUrl = `${BASE_URL}/threads/search`;
    let totalDeleted = 0;

    console.log('Starting thread cleanup...');

    while (true) {
        // Get the next page of threads
        console.log('Searching for threads...');
        const searchResponse = await fetch(searchUrl, {
            method: 'POST',
            headers,
            body: JSON.stringify({
                limit: 1000,
                select: ['thread_id']
            })
        });

        if (!searchResponse.ok) {
            throw new Error(`Search request failed: ${searchResponse.status} ${searchResponse.statusText}`);
        }

        const threads = await searchResponse.json();

        // If no threads found, we're done
        if (!threads || threads.length === 0) {
            console.log('No more threads found.');
            break;
        }

        console.log(`Found ${threads.length} threads to delete`);

        // Delete each thread
        for (const thread of threads) {
            try {
                const deleteUrl = `${BASE_URL}/threads/${thread.thread_id}`;
                const deleteResponse = await fetch(deleteUrl, {
                    method: 'DELETE',
                    headers
                });

                if (!deleteResponse.ok) {
                    console.error(`Failed to delete thread ${thread.thread_id}: ${deleteResponse.status} ${deleteResponse.statusText}`);
                } else {
                    totalDeleted++;
                }
            } catch (deleteError) {
                console.error(`Error deleting thread ${thread.thread_id}:`, deleteError.message);
            }
        }

        console.log(`Deleted ${threads.length} threads in this batch`);
    }

    console.log(`Thread cleanup completed. Total threads deleted: ${totalDeleted}`);
}

clean().catch(error => {
    console.error('Unhandled error:', error.message);
    process.exit(1);
});

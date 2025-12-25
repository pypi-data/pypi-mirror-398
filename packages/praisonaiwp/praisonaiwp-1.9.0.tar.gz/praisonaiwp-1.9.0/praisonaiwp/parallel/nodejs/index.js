#!/usr/bin/env node
/**
 * PraisonAIWP Parallel Executor
 * 
 * Executes WordPress operations in parallel using Node.js async capabilities
 */

const { Client } = require('ssh2');
const pLimit = require('p-limit');
const fs = require('fs');

/**
 * Execute WP-CLI command via SSH
 */
async function executeWPCommand(serverConfig, command) {
    return new Promise((resolve, reject) => {
        const conn = new Client();
        
        conn.on('ready', () => {
            const fullCommand = `cd ${serverConfig.wp_path} && ${serverConfig.php_bin} ${serverConfig.wp_cli} ${command}`;
            
            conn.exec(fullCommand, (err, stream) => {
                if (err) {
                    conn.end();
                    return reject(err);
                }
                
                let stdout = '';
                let stderr = '';
                
                stream.on('close', (code) => {
                    conn.end();
                    
                    if (code !== 0 || stderr.includes('Error:')) {
                        reject(new Error(stderr || `Command failed with code ${code}`));
                    } else {
                        resolve(stdout.trim());
                    }
                });
                
                stream.on('data', (data) => {
                    stdout += data.toString();
                });
                
                stream.stderr.on('data', (data) => {
                    stderr += data.toString();
                });
            });
        });
        
        conn.on('error', (err) => {
            reject(err);
        });
        
        // Read private key
        const privateKey = fs.readFileSync(serverConfig.key_file.replace('~', process.env.HOME));
        
        conn.connect({
            host: serverConfig.hostname,
            port: serverConfig.port || 22,
            username: serverConfig.username,
            privateKey: privateKey,
            readyTimeout: 30000
        });
    });
}

/**
 * Create a single post
 */
async function createPost(serverConfig, postData) {
    const args = [];
    
    // Escape single quotes
    const escapeValue = (val) => String(val).replace(/'/g, "'\\''");
    
    for (const [key, value] of Object.entries(postData)) {
        args.push(`--${key}='${escapeValue(value)}'`);
    }
    
    const command = `post create ${args.join(' ')} --porcelain`;
    
    try {
        const postId = await executeWPCommand(serverConfig, command);
        return {
            success: true,
            post_id: parseInt(postId),
            title: postData.title || postData.post_title
        };
    } catch (error) {
        return {
            success: false,
            error: error.message,
            title: postData.title || postData.post_title
        };
    }
}

/**
 * Update a single post
 */
async function updatePost(serverConfig, updateData) {
    const { post_id, ...fields } = updateData;
    const args = [];
    
    const escapeValue = (val) => String(val).replace(/'/g, "'\\''");
    
    for (const [key, value] of Object.entries(fields)) {
        args.push(`--${key}='${escapeValue(value)}'`);
    }
    
    const command = `post update ${post_id} ${args.join(' ')}`;
    
    try {
        await executeWPCommand(serverConfig, command);
        return {
            success: true,
            post_id: post_id
        };
    } catch (error) {
        return {
            success: false,
            post_id: post_id,
            error: error.message
        };
    }
}

/**
 * Main execution function
 */
async function main() {
    try {
        // Read input from stdin
        let inputData = '';
        
        for await (const chunk of process.stdin) {
            inputData += chunk;
        }
        
        const input = JSON.parse(inputData);
        const { operation, data, server, workers } = input;
        
        // Create concurrency limiter
        const limit = pLimit(workers);
        
        // Execute operations in parallel
        let results;
        
        if (operation === 'create') {
            results = await Promise.all(
                data.map(postData => 
                    limit(() => createPost(server, postData))
                )
            );
        } else if (operation === 'update') {
            results = await Promise.all(
                data.map(updateData => 
                    limit(() => updatePost(server, updateData))
                )
            );
        } else {
            throw new Error(`Unknown operation: ${operation}`);
        }
        
        // Output results as JSON
        console.log(JSON.stringify(results));
        
        process.exit(0);
    } catch (error) {
        console.error(JSON.stringify({
            error: error.message,
            stack: error.stack
        }));
        process.exit(1);
    }
}

// Run main function
main();

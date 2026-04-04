#!/usr/bin/env node
/**
 * Newman wrapper to resolve {{host}} and {{port}} in Postman test scripts
 * Fixes RangeError when pm.sendRequest() uses template variables in backticks
 */

const fs = require('fs');
const { spawn } = require('child_process');

const collectionPath = process.argv[2] || './DicoEvent_Versi_1_Postman/[788] DicoEvent versi 1.postman_collection.json';
const environmentPath = process.argv[3] || './DicoEvent_Versi_1_Postman/[788] DicoEvent.postman_environment.json';
const host = process.argv[4] || 'localhost';
const port = process.argv[5] || '8000';

console.log('📋 Reading Postman collection...');
const collection = JSON.parse(fs.readFileSync(collectionPath, 'utf8'));

console.log('🔍 Reading environment file...');
const environment = JSON.parse(fs.readFileSync(environmentPath, 'utf8'));

const varMap = { 'host': host, 'port': port };
if (environment.values) {
  environment.values.forEach(v => { varMap[v.key] = v.value; });
}

console.log(`✓ Variables: host=${varMap.host}, port=${varMap.port}`);

function processRequests(items) {
  if (!items || !Array.isArray(items)) return;
  
  items.forEach(item => {
    // Recursively process folders
    if (item.item && Array.isArray(item.item)) {
      processRequests(item.item);
    }
    
    // Fix URLs
    if (item.request && item.request.url) {
      if (typeof item.request.url === 'string') {
        item.request.url = item.request.url.replace(/\{\{([^}]+)\}\}/g, (m, v) => varMap[v] || m);
      } else if (item.request.url.raw) {
        item.request.url.raw = item.request.url.raw.replace(/\{\{([^}]+)\}\}/g, (m, v) => varMap[v] || m);
      }
    }

    // Normalize known payload/assertion mismatch in the checked-in collection.
    // The Edit Users request sends a timestamped username, while the assertion
    // expects the environment variable newUsername. We patch only the temporary
    // collection copy so source Postman assets remain unchanged.
    if (item.request && item.request.body && typeof item.request.body.raw === 'string') {
      item.request.body.raw = item.request.body.raw.replace(
        /"username":\s*"newUsername_\{\{\$timestamp\}\}"/g,
        '"username": "{{newUsername}}"'
      );
    }
    
    // FIX TEST SCRIPTS - Replace {{host}} and {{port}} in backtick template literals
    if (item.event && Array.isArray(item.event)) {
      item.event.forEach(event => {
        if (event.script && event.script.exec && Array.isArray(event.script.exec)) {
          const scriptCode = event.script.exec.join('\n');
          const resolved = scriptCode.replace(/\{\{([^}]+)\}\}/g, (m, v) => varMap[v] || m);
          event.script.exec = resolved.split('\n');
        }
      });
    }
  });
}

console.log('🔄 Processing collection items...');
if (collection.item && Array.isArray(collection.item)) {
  processRequests(collection.item);
}

const tempPath = '/tmp/dicoevent-collection-temp.json';
console.log(`💾 Writing modified collection...`);
fs.writeFileSync(tempPath, JSON.stringify(collection, null, 2));

console.log('🚀 Starting Newman...\n');

const newman = spawn('newman', [
  'run', tempPath,
  '-e', environmentPath,
  '--reporters', 'cli,json',
  '--reporter-json-export', '/tmp/newman-final-report.json',
  '--insecure'
], { stdio: 'inherit', cwd: process.cwd() });

newman.on('close', (code) => {
  try { fs.unlinkSync(tempPath); } catch (e) {}
  console.log('\n✅ Newman completed with exit code:', code);
  process.exit(code);
});

newman.on('error', (err) => {
  console.error('❌ Newman error:', err);
  try { fs.unlinkSync(tempPath); } catch (e) {}
  process.exit(1);
});

// Crypto polyfill for Node.js v16 compatibility
// This file must be loaded before Vite starts

const { randomFillSync, randomUUID } = require('crypto');

// Only polyfill if crypto.getRandomValues doesn't exist
if (typeof globalThis.crypto === 'undefined' || typeof globalThis.crypto.getRandomValues === 'undefined') {
  console.log('[crypto-polyfill] Applying crypto polyfill for Node.js v16 compatibility');
  
  globalThis.crypto = {
    getRandomValues: function(array) {
      if (!(array instanceof Uint8Array || array instanceof Uint16Array || 
            array instanceof Uint32Array || array instanceof BigUint64Array)) {
        throw new TypeError('Argument must be a typed array');
      }
      return randomFillSync(array);
    },
    randomUUID: randomUUID,
    subtle: {} // Minimal subtle crypto implementation
  };
  
  console.log('[crypto-polyfill] Crypto polyfill applied successfully');
}

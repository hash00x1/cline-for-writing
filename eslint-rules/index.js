// eslint-rules/index.js

// Polyfill for structuredClone if not available (for Node.js compatibility)
if (typeof structuredClone === 'undefined') {
  global.structuredClone = function(obj) {
    // Simple polyfill using JSON.parse/stringify for basic cloning
    // This is sufficient for the ESLint use case
    if (obj === null || typeof obj !== 'object') {
      return obj;
    }
    return JSON.parse(JSON.stringify(obj));
  };
}

const noProtobufObjectLiterals = require("./no-protobuf-object-literals")
const noGrpcClientObjectLiterals = require("./no-grpc-client-object-literals")

module.exports = {
	rules: {
		"no-protobuf-object-literals": noProtobufObjectLiterals,
		"no-grpc-client-object-literals": noGrpcClientObjectLiterals,
	},
	configs: {
		recommended: {
			plugins: ["local"],
			rules: {
				"local/no-protobuf-object-literals": "error",
				"local/no-grpc-client-object-literals": "error",
			},
		},
	},
}

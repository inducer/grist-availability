module.exports = {
  env: {
    browser: true,
    es2021: true,
  },
  parserOptions: {
    ecmaVersion: 13,
    sourceType: 'module',
  },
  rules: {
    'no-unused-vars': ['error', { varsIgnorePattern: '^_' }],
    'no-alert': 0
  },
};

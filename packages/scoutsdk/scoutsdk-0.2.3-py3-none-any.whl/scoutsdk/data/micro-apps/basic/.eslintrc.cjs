module.exports = {
  parser: '@typescript-eslint/parser',
  extends: [
    'react-app',
    'plugin:@typescript-eslint/recommended',
    'plugin:jsonc/base',
    'prettier',
  ],
  rules: {
    'func-style': ['error', 'expression'],
    'quotes': ['warn', 'single', {avoidEscape: true}],
    'prefer-arrow-callback': 'error',
    'no-console': 'warn',
    'no-var': 'error',
    'react/jsx-curly-brace-presence': ['error', {props: 'never', children: 'never'}],
    '@typescript-eslint/no-explicit-any': 'error',
    // "jsonc"
    'jsonc/sort-keys': ['error', 'asc'],
    'jsonc/quotes': ['error', 'double', {avoidEscape: false}],
    'react/self-closing-comp': ['error'],
  },
  overrides: [
    {
      files: ['*.json'],
      parser: 'jsonc-eslint-parser',
    },
  ],
};

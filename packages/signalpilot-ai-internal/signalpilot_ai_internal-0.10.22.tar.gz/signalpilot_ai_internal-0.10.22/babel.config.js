module.exports = {
  presets: [
    [
      '@babel/preset-env',
      {
        targets: {
          node: '18'
        }
      }
    ],
    '@babel/preset-typescript'
  ],
  plugins: [],
  env: {
    production: {
      plugins: [
        [
          'babel-plugin-transform-remove-console',
          {
            exclude: ['error', 'warn'] // Keep console.error and console.warn for production
          }
        ]
      ]
    }
  }
};

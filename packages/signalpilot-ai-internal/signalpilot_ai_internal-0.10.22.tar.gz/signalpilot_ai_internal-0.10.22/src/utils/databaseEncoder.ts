/**
 * Database credential encoding utilities
 * Similar to JWT token encoding, but specifically for database credentials
 * Note: This is minimal obfuscation, not encryption. It prevents plaintext storage.
 */
export class DatabaseEncoder {
  /**
   * Encode database credentials using base64 encoding
   * @param credentials The database credentials object to encode
   * @returns The base64 encoded credentials string
   */
  public static encode(credentials: any): string {
    if (!credentials) {
      return '';
    }

    try {
      // Convert to JSON string first, then encode
      const jsonString = JSON.stringify(credentials);
      const encoded = btoa(jsonString);

      console.log(
        '[DatabaseEncoder] ✅ Database credentials encoded successfully'
      );
      console.log('[DatabaseEncoder] Encoded length:', encoded.length);

      return encoded;
    } catch (error) {
      console.error(
        '[DatabaseEncoder] ❌ Failed to encode database credentials:',
        error
      );
      throw new Error('Failed to encode database credentials');
    }
  }

  /**
   * Decode base64 encoded database credentials
   * @param encodedCredentials The base64 encoded credentials to decode
   * @returns The decoded database credentials object
   */
  public static decode(encodedCredentials: string): any {
    if (!encodedCredentials) {
      return null;
    }

    try {
      // Decode from base64 then parse JSON
      const decoded = atob(encodedCredentials);
      const credentials = JSON.parse(decoded);

      return credentials;
    } catch (error) {
      console.error(
        '[DatabaseEncoder] ❌ Failed to decode database credentials:',
        error
      );
      throw new Error(
        'Failed to decode database credentials - data may be corrupted'
      );
    }
  }

  /**
   * Check if credentials appear to be base64 encoded
   * @param credentials The credentials to check
   * @returns True if the credentials appear to be base64 encoded
   */
  public static isEncoded(credentials: string): boolean {
    if (!credentials || typeof credentials !== 'string') {
      return false;
    }

    try {
      // Try to decode and see if it results in valid JSON
      const decoded = atob(credentials);
      JSON.parse(decoded);
      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * Validate that decoded credentials have required fields
   * @param credentials The credentials object to validate
   * @returns True if credentials have the required structure
   */
  public static validateCredentials(credentials: any): boolean {
    if (!credentials || typeof credentials !== 'object') {
      return false;
    }

    // Check for required fields that all database credentials should have
    const requiredFields = [
      'id',
      'name',
      'type',
      'host',
      'port',
      'database',
      'username',
      'password'
    ];

    // eslint-disable-next-line no-prototype-builtins
    return requiredFields.every(field => credentials.hasOwnProperty(field));
  }

  /**
   * Safely encode credentials with validation
   * @param credentials The credentials to encode
   * @returns The encoded credentials or throws an error
   */
  public static safeEncode(credentials: any): string {
    if (!this.validateCredentials(credentials)) {
      throw new Error(
        'Invalid credentials structure - missing required fields'
      );
    }

    return this.encode(credentials);
  }

  /**
   * Safely decode credentials with validation
   * @param encodedCredentials The encoded credentials to decode
   * @returns The decoded and validated credentials or throws an error
   */
  public static safeDecode(encodedCredentials: string): any {
    const credentials = this.decode(encodedCredentials);

    if (!this.validateCredentials(credentials)) {
      throw new Error(
        'Decoded credentials are invalid - missing required fields'
      );
    }

    return credentials;
  }

  /**
   * Create a masked version of credentials for logging (sensitive fields hidden)
   * @param credentials The credentials to mask
   * @returns A masked version safe for logging
   */
  public static maskForLogging(credentials: any): any {
    if (!credentials || typeof credentials !== 'object') {
      return credentials;
    }

    const masked = { ...credentials };

    // Mask sensitive fields
    if (masked.password) {
      masked.password = '***masked***';
    }
    if (masked.username) {
      masked.username = masked.username.substring(0, 2) + '***';
    }

    return masked;
  }
}

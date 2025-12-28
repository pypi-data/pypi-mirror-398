/**
 * Simple encoding utilities for JWT token obfuscation
 * Note: This is minimal obfuscation, not encryption. It just prevents plaintext storage.
 */
export class TokenEncoder {
  /**
   * Encode a JWT token using base64 encoding
   * @param token The JWT token to encode
   * @returns The base64 encoded token
   */
  public static encode(token: string): string {
    if (!token) {
      return '';
    }

    try {
      // Convert to base64
      return btoa(token);
    } catch (error) {
      console.warn('[TokenEncoder] Failed to encode token:', error);
      return token; // Return original if encoding fails
    }
  }

  /**
   * Decode a base64 encoded JWT token
   * @param encodedToken The base64 encoded token to decode
   * @returns The decoded JWT token
   */
  public static decode(encodedToken: string): string {
    if (!encodedToken) {
      return '';
    }

    // If it's already a JWT (contains dots), return as is
    if (this.looksLikeJWT(encodedToken)) {
      return encodedToken;
    }

    try {
      // Decode from base64
      const decoded = atob(encodedToken);

      // For development/testing: If it's a simple string like "test", return it
      // For production: Verify that the decoded string looks like a JWT
      if (this.looksLikeJWT(decoded) || decoded.length < 50) {
        // Either a valid JWT or a short test token
        return decoded;
      } else {
        console.warn(
          '[TokenEncoder] Decoded token does not look like a JWT or test token'
        );
        return encodedToken; // Return original if decoded doesn't look valid
      }
    } catch (error) {
      console.warn('[TokenEncoder] Failed to decode token:', error);
      return encodedToken; // Return original if decoding fails (might already be plaintext)
    }
  }

  /**
   * Check if a token appears to be base64 encoded
   * @param token The token to check
   * @returns True if the token appears to be base64 encoded
   */
  public static isEncoded(token: string): boolean {
    if (!token) {
      return false;
    }

    try {
      // A JWT token has the format: xxxxx.yyyyy.zzzzz
      // If it's base64 encoded, it won't have dots
      if (token.includes('.')) {
        return false; // Likely a raw JWT
      }

      // Try to decode and see if it looks like a JWT
      const decoded = atob(token);
      return this.looksLikeJWT(decoded);
    } catch (error) {
      return false;
    }
  }

  /**
   * Check if a string looks like a JWT token
   * @param token The token to check
   * @returns True if the token looks like a JWT
   */
  private static looksLikeJWT(token: string): boolean {
    if (!token) {
      return false;
    }

    // JWT tokens have exactly 3 parts separated by dots
    const parts = token.split('.');
    return parts.length === 3 && parts.every(part => part.length > 0);
  }
}

/**
 * Utility functions for the complex fixture.
 */

/**
 * Validate a JWT token.
 */
export async function validateToken(token: string): Promise<boolean> {
    if (!token || token.length < 10) {
        return false;
    }

    // Simplified validation
    const parts = token.split('.');
    return parts.length === 3;
}

/**
 * Hash a password (simplified).
 */
export function hashPassword(password: string): string {
    return Buffer.from(password).toString('base64');
}

/**
 * Generate a random ID.
 */
export function generateId(): string {
    return Math.random().toString(36).substring(2, 15);
}

/**
 * Format date for display.
 */
export function formatDate(date: Date): string {
    return date.toISOString();
}

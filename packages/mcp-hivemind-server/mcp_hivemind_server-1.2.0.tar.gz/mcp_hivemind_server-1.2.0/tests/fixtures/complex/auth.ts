/**
 * Complex authentication module for testing.
 */

import { createClient } from '@supabase/supabase-js';
import { validateToken } from './utils';

interface User {
    id: string;
    email: string;
    role: 'admin' | 'user';
}

interface AuthResult {
    success: boolean;
    user?: User;
    error?: string;
}

/**
 * Validate user session token.
 */
export async function validateSession(token: string): Promise<boolean> {
    if (!token) {
        return false;
    }
    
    try {
        const isValid = await validateToken(token);
        return isValid;
    } catch (error) {
        console.error('Session validation failed:', error);
        return false;
    }
}

/**
 * Authenticate user with email and password.
 */
export async function authenticateUser(
    email: string,
    password: string
): Promise<AuthResult> {
    // Input validation
    if (!email || !password) {
        return { success: false, error: 'Email and password required' };
    }
    
    // Check rate limiting
    if (await isRateLimited(email)) {
        return { success: false, error: 'Too many attempts' };
    }
    
    try {
        // Supabase auth
        const supabase = createClient(
            process.env.SUPABASE_URL!,
            process.env.SUPABASE_KEY!
        );
        
        const { data, error } = await supabase.auth.signInWithPassword({
            email,
            password,
        });
        
        if (error) {
            return { success: false, error: error.message };
        }
        
        return {
            success: true,
            user: {
                id: data.user.id,
                email: data.user.email!,
                role: 'user',
            },
        };
    } catch (error) {
        return { success: false, error: 'Authentication failed' };
    }
}

/**
 * Check if user is rate limited.
 */
async function isRateLimited(email: string): Promise<boolean> {
    // Simplified rate limiting check
    return false;
}

/**
 * Create a new user session.
 */
export function createSession(user: User): string {
    const payload = {
        userId: user.id,
        email: user.email,
        role: user.role,
        exp: Date.now() + 3600000, // 1 hour
    };
    
    return Buffer.from(JSON.stringify(payload)).toString('base64');
}

export default class AuthService {
    private supabase;
    
    constructor(url: string, key: string) {
        this.supabase = createClient(url, key);
    }
    
    async signIn(email: string, password: string): Promise<AuthResult> {
        return authenticateUser(email, password);
    }
    
    async signOut(): Promise<void> {
        await this.supabase.auth.signOut();
    }
}

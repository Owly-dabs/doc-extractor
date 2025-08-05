/** Utility function to subtract numbers */
export function subtract(a: number, b: number): number {
    return a - b;
}

/** A typed interface for a user */
export interface IUser {
    /** User ID */
    id: number;
    
    /** User name */
    name: string;
}

/** A class to manage users */
export class UserManager {
    /** List of users */
    private users: IUser[];

    /** Initialize user manager */
    constructor() {
        this.users = [];
    }

    /** Add a user */
    addUser(user: IUser): void {
        this.users.push(user);
    }
}

// --- Non-exported items below ---

/** Multiply two numbers */
function multiply(x: number, y: number): number {
    return x * y;
}

/** Internal user role enum */
enum Role {
    Admin,
    Guest,
    User,
}

/** Internal utility type for ID tracking */
interface InternalIDMap {
    [key: string]: number;
}

/** Local-only user store */
class UserStore {
    private store: InternalIDMap = {};

    /** Add ID to store */
    add(id: string, value: number) {
        this.store[id] = value;
    }
}

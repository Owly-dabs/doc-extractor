/** Adds two numbers */
function add(a, b) {
    return a + b;
}

/** Represents a user */
class User {
    /** The user's ID */
    constructor(id) {
        this.id = id;
    }

    /** Get the user ID */
    getId() {
        return this.id;
    }
}

// This is a helper function
function log(message) {
    console.log(message);
}

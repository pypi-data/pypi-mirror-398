/**
 * Parse Dsp format (human-readable) to Ds format (internal S-expression)
 * @param input - The Dsp format string to parse
 * @returns The Ds format string
 */
export function parse(input: string): string;

/**
 * Unparse Ds format (internal S-expression) to Dsp format (human-readable)
 * @param input - The Ds format string to unparse
 * @returns The Dsp format string
 */
export function unparse(input: string): string;

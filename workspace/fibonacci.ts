function fibonacci(n: number): number[] {
    const fib: number[] = [0, 1];
    for (let i = 2; i < n; i++) {
        fib[i] = fib[i - 1] + fib[i - 2];
    }
    return fib.slice(0, n);
}

// Ejemplo de uso
const n = 10; // Cambia este valor para obtener más o menos números de Fibonacci
console.log(fibonacci(n));

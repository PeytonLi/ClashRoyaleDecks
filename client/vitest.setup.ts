import { AsyncLocalStorage } from "node:async_hooks";

type GlobalWithAsyncLocalStorage = typeof globalThis & {
  AsyncLocalStorage?: typeof AsyncLocalStorage;
};

(globalThis as GlobalWithAsyncLocalStorage).AsyncLocalStorage ??= AsyncLocalStorage;

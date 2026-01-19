declare module 'luaparse' {
  interface ParseOptions {
    luaVersion?: '5.1' | '5.2' | '5.3';
    locations?: boolean;
    ranges?: boolean;
    scope?: boolean;
    comments?: boolean;
  }

  interface ParseError {
    message: string;
    loc?: {
      line: number;
      column: number;
    };
    location?: {
      line: number;
      column: number;
    };
  }

  function luaparse(code: string, options?: ParseOptions): any;
  export = luaparse;
}

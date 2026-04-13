declare const process: {
  env: Record<string, string | undefined>;
};

declare module "*.css?url" {
  const href: string;
  export default href;
}

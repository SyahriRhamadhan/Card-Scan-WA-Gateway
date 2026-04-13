import type { LinksFunction, MetaFunction } from "@remix-run/node";
import { Links, Meta, Outlet, Scripts, ScrollRestoration } from "@remix-run/react";

import stylesHref from "./styles/tailwind.css?url";

export const meta: MetaFunction = () => [
  { title: "Cardscan" },
  {
    name: "description",
    content: "Upload kartu nama, OCR, lalu kirim data kontak ke WhatsApp gateway v2.",
  },
];

export const links: LinksFunction = () => [{ rel: "stylesheet", href: stylesHref }];

export default function App() {
  return (
    <html lang="id">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <Meta />
        <Links />
      </head>
      <body>
        <Outlet />
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}

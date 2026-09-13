import { parsePdf } from "./parsePdf";

export const MAX_CHARS = 40000;

export async function extractTextFromRequest(req: Request): Promise<string> {
  const contentType = req.headers.get("content-type") ?? "";

  if (contentType.includes("multipart/form-data")) {
    const formData = await req.formData();
    const file = formData.get("file");

    if (!file || !(file instanceof Blob)) {
      throw new Error("No file provided in form data");
    }

    const buffer = Buffer.from(await file.arrayBuffer());
    const text = await parsePdf(buffer);
    return text.slice(0, MAX_CHARS);
  }

  if (contentType.includes("application/json")) {
    const body = await req.json();
    const text: string | undefined = body?.text;

    if (!text) {
      throw new Error("No text provided in request body");
    }

    return text.slice(0, MAX_CHARS);
  }

  throw new Error("Unsupported content type");
}

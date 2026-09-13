// eslint-disable-next-line @typescript-eslint/no-require-imports
const pdf = require("pdf-parse") as (
  buffer: Buffer
) => Promise<{ text: string }>;

export async function parsePdf(buffer: Buffer): Promise<string> {
  if (buffer.length === 0) {
    throw new Error("PDF buffer is empty");
  }

  const data = await pdf(buffer);

  if (!data.text || data.text.trim().length === 0) {
    throw new Error(
      "Could not extract text from this PDF. Please use a text-based PDF or paste the text directly."
    );
  }

  return data.text;
}

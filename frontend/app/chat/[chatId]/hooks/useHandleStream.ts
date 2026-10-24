import { useChatContext } from "@/lib/context";

import { ChatMessage } from "../types";

// eslint-disable-next-line @typescript-eslint/explicit-module-boundary-types
export const useHandleStream = () => {
  const { updateStreamingHistory } = useChatContext();

  const handleStream = async (
    reader: ReadableStreamDefaultReader<Uint8Array>,
    onFirstChunk: () => void
  ): Promise<void> => {
    const decoder = new TextDecoder("utf-8");
    let isFirstChunk = true;
    let incompleteEvent = "";

    const handleEvent = (event: string) => {
      const data = event
        .split(/\r?\n/)
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice("data:".length).trimStart())
        .join("\n");

      if (data === "") {
        return;
      }

      try {
        updateStreamingHistory(JSON.parse(data) as ChatMessage);
      } catch (error) {
        console.error("Error parsing stream event", error);
      }
    };

    const handleStreamRecursively = async () => {
      const { done, value } = await reader.read();

      if (done) {
        incompleteEvent += decoder.decode();
        if (incompleteEvent.trim() !== "") {
          handleEvent(incompleteEvent);
        }

        return;
      }

      if (isFirstChunk) {
        isFirstChunk = false;
        onFirstChunk();
      }

      incompleteEvent += decoder.decode(value, { stream: true });
      const events = incompleteEvent.split(/\r?\n\r?\n/);
      incompleteEvent = events.pop() ?? "";
      events.forEach(handleEvent);

      await handleStreamRecursively();
    };

    await handleStreamRecursively();
  };

  return {
    handleStream,
  };
};

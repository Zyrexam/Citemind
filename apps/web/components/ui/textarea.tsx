import * as React from "react";
import { cn } from "@/lib/utils";

export const Textarea = React.forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => (
    <textarea
      ref={ref}
      className={cn(
        "flex w-full resize-none border-0 bg-transparent p-0 font-text text-[1.0625rem] leading-7 text-ink",
        "placeholder:text-ink-faint/85 focus-visible:outline-none",
        className
      )}
      {...props}
    />
  )
);
Textarea.displayName = "Textarea";

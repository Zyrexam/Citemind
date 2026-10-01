import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 font-ui text-[13px] tracking-[0.02em] transition-colors duration-75 disabled:opacity-45 disabled:pointer-events-none",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/88",
        quiet: "text-ink-soft hover:text-ink border-b border-rule hover:border-rule-strong",
        ghost: "text-ink-soft hover:text-ink",
      },
      size: {
        default: "h-10 px-5 rounded-[3px]",
        quiet: "h-9 px-1",
        sm: "h-8 px-3 rounded-[3px] text-[12px]",
        icon: "h-9 w-9 rounded-[3px]",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button ref={ref} className={cn(buttonVariants({ variant, size, className }))} {...props} />
  )
);
Button.displayName = "Button";

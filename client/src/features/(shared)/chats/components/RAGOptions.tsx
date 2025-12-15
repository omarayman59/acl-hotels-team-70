// embedding / basemodel or both
// choose embedding model if model choosen
// LLM model choice

"use client";

import { zodResolver } from "@hookform/resolvers/zod";

import { useEffect } from "react";
import { useChats } from "../utils/provider";
import { useForm, useWatch } from "react-hook-form";

import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormMessage,
} from "@/components/ui/form";
import { Checkbox } from "@/components/ui/checkbox";

import { RAGOptionsSchema, type RAGOptionsType } from "../types";
import {
  Select,
  SelectValue,
  SelectTrigger,
  SelectItem,
  SelectContent,
} from "@/components/ui/select";

export const RAGOptions = () => {
  const { ragOptions, setRAGOptions } = useChats();

  const form = useForm<RAGOptionsType>({
    resolver: zodResolver(RAGOptionsSchema),
    defaultValues: ragOptions,
  });

  // watch form values and update context whenever they change
  const selection = useWatch({ control: form.control, name: "selection" });
  const embeddingModel = useWatch({
    control: form.control,
    name: "embeddingModel",
  });
  const LLMModel = useWatch({ control: form.control, name: "LLMModel" });

  useEffect(() => {
    if (form.formState.isValid) {
      setRAGOptions({
        selection: selection || [],
        embeddingModel,
        LLMModel: LLMModel || "gpt-5-mini-2025-08-07",
      });
    }
  }, [
    selection,
    embeddingModel,
    LLMModel,
    form.formState.isValid,
    setRAGOptions,
  ]);

  return (
    <div className="w-full space-y-4">
      <Form {...form}>
        <form className="space-y-6">
          <FormField
            control={form.control}
            name="selection"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Selection</FormLabel>
                <FormControl>
                  <div className="flex gap-4">
                    <div className="flex items-center gap-2">
                      <Checkbox
                        checked={field.value?.includes("semantic")}
                        onCheckedChange={(checked) => {
                          const current = field.value || [];
                          field.onChange(
                            checked
                              ? [
                                  ...current.filter((v) => v !== "semantic"),
                                  "semantic",
                                ]
                              : current.filter((v) => v !== "semantic")
                          );
                        }}
                      />
                      <FormLabel className="cursor-pointer">Semantic</FormLabel>
                    </div>
                    <div className="flex items-center gap-2">
                      <Checkbox
                        checked={field.value?.includes("baseline")}
                        onCheckedChange={(checked) => {
                          const current = field.value || [];
                          field.onChange(
                            checked
                              ? [
                                  ...current.filter((v) => v !== "baseline"),
                                  "baseline",
                                ]
                              : current.filter((v) => v !== "baseline")
                          );
                        }}
                      />
                      <FormLabel className="cursor-pointer">Baseline</FormLabel>
                    </div>
                  </div>
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          {selection?.includes("semantic") && (
            <FormField
              control={form.control}
              name="embeddingModel"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Embedding Model</FormLabel>
                  <FormControl>
                    <Select
                      {...field}
                      value={field.value || ""}
                      onValueChange={field.onChange}
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select an embedding model" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="SBERT">SBERT</SelectItem>
                        <SelectItem value="MiniLM">MiniLM</SelectItem>
                      </SelectContent>
                    </Select>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          )}

          <FormField
            control={form.control}
            name="LLMModel"
            render={({ field }) => (
              <FormItem>
                <FormLabel>LLM Model</FormLabel>
                <FormControl>
                  <Select
                    {...field}
                    value={field.value || ""}
                    onValueChange={field.onChange}
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select an LLM model" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="gpt-5-mini-2025-08-07">
                        gpt-5-mini
                      </SelectItem>
                      <SelectItem value="gpt-4.1">gpt-4.1</SelectItem>
                      <SelectItem value="gpt-4o">gpt-4o</SelectItem>
                    </SelectContent>
                  </Select>
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </form>
      </Form>
    </div>
  );
};

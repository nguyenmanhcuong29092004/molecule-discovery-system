/**
 * Start Run Page
 * 
 * Form for creating a new molecule discovery run
 */

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { useCreateRun } from '@/hooks/useCreateRun';
import { parseSMILESText } from '@/lib/api/runs';
import { runFormSchema, type RunFormValues } from '@/lib/validation/runFormSchema';
import { DEFAULT_FORM_VALUES } from '@/types/run';
import type { CreateRunRequest } from '@/types/run';

import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';

export default function StartRunPage() {
  const { toast } = useToast();

  const form = useForm<RunFormValues>({
    resolver: zodResolver(runFormSchema),
    defaultValues: DEFAULT_FORM_VALUES,
  });

  const createRunMutation = useCreateRun({
    onSuccess: (data) => {
      toast({
        title: 'Run Created Successfully',
        description: `Task ${data.task_id} has been queued. Redirecting to dashboard...`,
      });
      // Navigation handled by hook
    },
    onError: (error) => {
      toast({
        title: 'Error Creating Run',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  const onSubmit = (values: RunFormValues) => {
    // Transform form data to API format
    const request: CreateRunRequest = {
      config: {
        objective: values.objective,
        seed_smiles: parseSMILESText(values.seed_smiles_text),
        rounds: values.rounds,
        candidates_per_round: values.candidates_per_round,
        top_k: values.top_k,
        constraints: {
          max_mw: values.max_mw,
          max_logp: values.max_logp,
          max_hbd: values.max_hbd,
          max_hba: values.max_hba,
          max_tpsa: values.max_tpsa,
          max_violations: values.max_violations,
        },
      },
    };

    createRunMutation.mutate(request);
  };

  const isSubmitting = createRunMutation.isPending;

  return (
    <div className="container mx-auto py-8 px-4 max-w-4xl">
      <Card>
        <CardHeader>
          <CardTitle>Start New Molecule Generation</CardTitle>
          <CardDescription>
            Configure and launch a new molecule discovery run
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              {/* Objective */}
              <FormField
                control={form.control}
                name="objective"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Objective <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="E.g., Generate drug-like molecules with good CNS penetration"
                        className="resize-none"
                        rows={3}
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>
                      Describe the goal of this molecule generation run (10-500 characters)
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Seed SMILES */}
              <FormField
                control={form.control}
                name="seed_smiles_text"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Seed SMILES <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="CCO&#10;c1ccccc1&#10;CC(C)C"
                        className="font-mono resize-none"
                        rows={5}
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>
                      Enter SMILES strings (one per line, 1-10 molecules)
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Parameters Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <FormField
                  control={form.control}
                  name="rounds"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>
                        Rounds <span className="text-destructive">*</span>
                      </FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          min={1}
                          max={20}
                          {...field}
                          onChange={(e) => field.onChange(parseInt(e.target.value, 10))}
                        />
                      </FormControl>
                      <FormDescription>1-20</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="candidates_per_round"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>
                        Candidates/Round <span className="text-destructive">*</span>
                      </FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          min={10}
                          max={500}
                          {...field}
                          onChange={(e) => field.onChange(parseInt(e.target.value, 10))}
                        />
                      </FormControl>
                      <FormDescription>10-500</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="top_k"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>
                        Top K <span className="text-destructive">*</span>
                      </FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          min={1}
                          max={100}
                          {...field}
                          onChange={(e) => field.onChange(parseInt(e.target.value, 10))}
                        />
                      </FormControl>
                      <FormDescription>1-100</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              {/* Constraints Section */}
              <div className="space-y-4">
                <div>
                  <h3 className="text-lg font-medium">Constraints</h3>
                  <p className="text-sm text-muted-foreground">
                    Molecular property constraints for filtering
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <FormField
                    control={form.control}
                    name="max_mw"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>
                          Max MW <span className="text-destructive">*</span>
                        </FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            min={0}
                            max={1000}
                            step={0.1}
                            {...field}
                            onChange={(e) => field.onChange(parseFloat(e.target.value))}
                          />
                        </FormControl>
                        <FormDescription>0-1000 Da</FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="max_logp"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>
                          Max LogP <span className="text-destructive">*</span>
                        </FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            min={-5}
                            max={10}
                            step={0.1}
                            {...field}
                            onChange={(e) => field.onChange(parseFloat(e.target.value))}
                          />
                        </FormControl>
                        <FormDescription>-5 to 10</FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="max_hbd"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>
                          Max HBD <span className="text-destructive">*</span>
                        </FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            min={0}
                            max={20}
                            {...field}
                            onChange={(e) => field.onChange(parseInt(e.target.value, 10))}
                          />
                        </FormControl>
                        <FormDescription>0-20</FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="max_hba"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>
                          Max HBA <span className="text-destructive">*</span>
                        </FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            min={0}
                            max={30}
                            {...field}
                            onChange={(e) => field.onChange(parseInt(e.target.value, 10))}
                          />
                        </FormControl>
                        <FormDescription>0-30</FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="max_tpsa"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>
                          Max TPSA <span className="text-destructive">*</span>
                        </FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            min={0}
                            max={300}
                            step={0.1}
                            {...field}
                            onChange={(e) => field.onChange(parseFloat(e.target.value))}
                          />
                        </FormControl>
                        <FormDescription>0-300 Ų</FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="max_violations"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>
                          Max Violations <span className="text-destructive">*</span>
                        </FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            min={0}
                            max={5}
                            {...field}
                            onChange={(e) => field.onChange(parseInt(e.target.value, 10))}
                          />
                        </FormControl>
                        <FormDescription>0-5</FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
              </div>

              {/* Submit Button */}
              <Button
                type="submit"
                className="w-full"
                size="lg"
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating Run...
                  </>
                ) : (
                  'Start Generation'
                )}
              </Button>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
}
import { Button } from "@/components/ui/button";
import { WTAAlternativeCard } from "@/components/ui/wta-alternatives-grid";
import { useStreamContext } from "@/providers/Stream";
import { Check, X } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

interface Assignment {
  AssetName: string
  TargetName: string
  WeaponUsed: string
  KillProbability: number
  ReleasePoints: Record<string, any>
}

interface WTAAlternative {
  AlternativeNumber: number
  AlternativeName: string
  Assignments: Assignment[]
}


export interface WTAInterrupt {
  type: string;
  alternative: WTAAlternative;
  selected_alternative_name: string;
}

export function isWTAInterruptSchema(
  value: unknown,
): value is WTAInterrupt | WTAInterrupt[] {
  const valueAsObject = Array.isArray(value) ? value[0] : value;
  const isValid =

    valueAsObject &&
    typeof valueAsObject === "object" &&
    "type" in valueAsObject &&
    valueAsObject.type === "WTAInterrupt" &&
    "alternative" in valueAsObject &&
    typeof valueAsObject.alternative === "object"
    && "selected_alternative_name" in valueAsObject &&
    typeof valueAsObject.selected_alternative_name === "string";

  return isValid;
}


export function WTAInterruptView({
  interrupt,
}: {
  interrupt: Record<string, any> | Record<string, any>[];
}) {
  const [loading, setLoading] = useState(false);
  const thread = useStreamContext();

  // Extract the alternative from the interrupt data
  const getAlternative = (): WTAAlternative | null => {
    if (Array.isArray(interrupt)) {
      // If it's an array, look for the first item with alternative data
      const item = interrupt.find(item => item.alternative);
      return item?.alternative || null;
    } else {
      // If it's a single object, check if it has alternative data
      return interrupt.alternative || null;
    }
  };

  const alternative = getAlternative();

  const selected_alternative_name = Array.isArray(interrupt)
    ? interrupt[0].selected_alternative_name
    : interrupt.selected_alternative_name;

  if (!alternative) {
    // Fallback to original display if no alternative data is found
    return (
      <div className="overflow-hidden rounded-lg border border-gray-200">
        <div className="border-b border-gray-200 bg-gray-50 px-4 py-2">
          <h3 className="font-medium text-gray-900">Human Interrupt</h3>
        </div>
        <div className="p-3 bg-gray-100">
          <code className="rounded bg-gray-50 px-2 py-1 font-mono text-sm">
            {JSON.stringify(interrupt, null, 2)}
          </code>
        </div>
      </div>
    );
  }

  const handleApprove = async () => {
    setLoading(true);
    try {
      // Submit the response with approval
      thread.submit(
        {},
        {
          command: {
            resume: [
              {
                type: "accept",
              },
            ],
          },
        },
      );

      toast("Success", {
        description: "WTA Alternative approved successfully.",
        duration: 5000,
      });
    } catch (e: any) {
      console.error("Error approving WTA alternative", e);
      toast.error("Error", {
        description: "Failed to approve WTA alternative.",
        richColors: true,
        closeButton: true,
        duration: 5000,
      });
    }
    setLoading(false);
  };

  const handleReject = async () => {
    setLoading(true);
    try {
      // Submit the response with rejection
      thread.submit(
        {},
        {
          command: {
            resume: [
              {
                type: "reject",
              },
            ],
          },
        },
      );

      toast("Success", {
        description: "WTA Alternative rejected successfully.",
        duration: 5000,
      });
    } catch (e: any) {
      console.error("Error rejecting WTA alternative", e);
      toast.error("Error", {
        description: "Failed to reject WTA alternative.",
        richColors: true,
        closeButton: true,
        duration: 5000,
      });
    }
    setLoading(false);
  };

  return (
    <div className="space-y-4">
      <div className=" bg-yellow-300 px-4 py-2 rounded-lg">
        <h3 className="font-medium text-gray-900">&#x1F6D1; Double confirmation required</h3>
      </div>

      <div className="px-4">
        <WTAAlternativeCard alternative={alternative} index={alternative.AlternativeNumber} />
      </div>

      <div className="flex justify-center gap-4 px-4 pb-4">
        <Button
          onClick={handleReject}
          disabled={loading}
          variant="outline"
          className="flex items-center gap-2 text-red-600 border-red-600 hover:bg-red-50 hover:text-red-700 disabled:opacity-50"
        >
          <X className="w-4 h-4" />
          Reject
        </Button>
        <Button
          onClick={handleApprove}
          disabled={loading}
          className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white disabled:opacity-50"
        >
          <Check className="w-4 h-4" />
          Approve
        </Button>
      </div>
    </div>
  );
}

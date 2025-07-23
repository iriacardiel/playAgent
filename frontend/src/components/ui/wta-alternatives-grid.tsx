import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

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

interface WTAAlternativeCardProps {
  alternative: WTAAlternative
  index: number
}

export function WTAAlternativeCard({ alternative, index }: WTAAlternativeCardProps) {
  const formatProbability = (prob: number) => `${(prob * 100).toFixed(1)}%`

  return (
    <Card className="h-full border-border shadow-sm bg-muted/100 dark:bg-muted/100 p-2 gap-4">
      <CardHeader className="pb-0 pt-1 px-2">
        <CardTitle className="flex items-center justify-between text-xs">
          <Badge
            variant="outline"
            className="rounded-full w-8 h-8 flex items-center justify-center border-blue-500 border-3 text-blue-500 font-bold bg-muted/100 dark:border-gray-300 dark:text-gray-300 dark:bg-muted/100"
          >
            {alternative.AlternativeName}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0 pb-1 px-2">
        <div>
          <h4 className="font-semibold mb-0.5 textmd">Assignments</h4>
          <div className="space-y-1.5">
            {alternative.Assignments.map((assignment, idx) => (
              <div
                key={idx}
                className="border border-border rounded-lg p-1 bg-background/80"
              >
                <div className="flex justify-between items-start mb-0.5">
                  <span className="font-medium text-xs pr-1 break-words">
                    <p>
                      <span className="text-gray-700 dark:text-gray-300">Asset:</span>{" "}
                      <span className="font-bold text-gray-700 dark:text-gray-300">{assignment.AssetName}</span>
                    </p>
                  </span>
                  <Badge className="text-xs shrink-0 py-0 px-1 whitespace-nowrap bg-slate-700 text-white dark:bg-blue-400">
                    {formatProbability(assignment.KillProbability)}
                  </Badge>
                </div>
                <div className="text-xs text-muted-foreground">
                  <div className="break-words">
                    <p>
                      <span className="text-gray-700 dark:text-gray-300">Target:</span>{" "}
                      <span className="font-bold text-gray-700 dark:text-gray-300">{assignment.TargetName}</span>
                    </p>
                  </div>
                  <div className="break-words">
                    <p>
                      <span className="text-gray-700 dark:text-gray-300">Weapon:</span>{" "}
                      <span className="font-bold text-gray-700 dark:text-gray-300">{assignment.WeaponUsed}</span>
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export function WTAAlternativesGrid(alternatives: WTAAlternative[]) {
  return (
    <div
      style={{
        width: "80vw",
        marginLeft: "-10vw",
      }}
    >
      <div
        className="grid gap-2 justify-center"
        style={{
          gridTemplateColumns: "repeat(auto-fit, minmax(150px, 260px))",
          maxWidth: "calc(4 * 260px + 3 * 0.5rem)",
          margin: "0 auto",
        }}
      >
        {alternatives.map((alternative: WTAAlternative, index: number) => (
          <div key={index} className="w-full">
            <WTAAlternativeCard alternative={alternative} index={index} />
          </div>
        ))}
      </div>
    </div>
  )
}

export default WTAAlternativesGrid
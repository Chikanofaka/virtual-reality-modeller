/** Ordered, plan-owned interaction objectives. No browser or scene dependencies. */
export function createGameplay(gameplay) {
  const enabled=gameplay!==undefined;
  const objectives=enabled?gameplay.objectives.map(objective=>({...objective})):[];
  const completionMessage=gameplay?.completionMessage||'All objectives complete — explore freely.';
  let index=0;
  return {
    enabled,
    completionMessage,
    reset(){index=0;},
    interact(targetId){
      if(!enabled||index>=objectives.length||objectives[index].targetId!==targetId)return false;
      index++;return true;
    },
    snapshot(){return {
      enabled,index,total:objectives.length,complete:enabled&&index===objectives.length,
      currentObjective:objectives[index]?{...objectives[index]}:null,
      completedObjectiveIds:objectives.slice(0,index).map(objective=>objective.id)
    };}
  };
}

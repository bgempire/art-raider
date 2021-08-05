import bge

from bge.types import *
from mathutils import Vector
from random import random


DEBUG = 0
GUARD_MOV_SPEED = 0.025
GUARD_CHASE_DISTANCE = 3.0
GUARD_ATTACK_DISTANCE = 0.75
GUARD_ACTION_INTERVAL = 2.0
GUARD_DEFAULT_PROPS = {
    "Direction" : "R",
    "Moving" : False,
    "Action" : "",
    "Alerted" : False,
}
GUARD_ANIMS = {
    "Idle" : (0, 59),
    "Walk" : (70, 89),
    "Attack" : (100, 120),
}


def main(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner
    
    always = cont.sensors["Always"] # type: SCA_AlwaysSensor
    
    if not own.groupObject:
        own.endObject()
        return
    
    if always.positive:
        
        if always.status == bge.logic.KX_SENSOR_JUST_ACTIVATED:
            initGuard(cont)
            
        setProps(cont)
        processAnimation(cont)
        processMovement(cont)


def initGuard(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner
    
    for prop in GUARD_DEFAULT_PROPS.keys():
        own[prop] = GUARD_DEFAULT_PROPS[prop]
        
    if DEBUG:
        for prop in own.getPropertyNames():
            own.addDebugProperty(prop)


def setProps(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner
    player = own.scene["Player"] if "Player" in own.scene else None # type: KX_GameObject
    exclamation = own.childrenRecursive["GuardExclamation"]
    
    if player:
        rayVec = Vector([1, 0, 0])
        if own["Direction"] == "L":
            rayVec.x *= -1
            
        ray = own.rayCast(own.worldPosition + rayVec, own, 1, "OBSTACLE")
        
        if not ray[0]:
            if own["Alerted"]:
                
                if player.worldPosition.x < own.worldPosition.x:
                    own["Direction"] = "L"
                else:
                    own["Direction"] = "R"
                    
                if own.getDistanceTo(player) > GUARD_CHASE_DISTANCE  or player["Dead"]:
                    own["Alerted"] = False
                    exclamation.visible = False
                    
                elif own.getDistanceTo(player) < GUARD_ATTACK_DISTANCE:
                    own["Action"] = "Attack"
                    
                else:
                    own["Moving"] = True
                    
            elif own.getDistanceTo(player) < GUARD_CHASE_DISTANCE and not player["Dead"]:
                if own["Direction"] == "L" and player.worldPosition.x < own.worldPosition.x \
                or own["Direction"] == "R" and player.worldPosition.x > own.worldPosition.x:
                    ray = own.rayCast(own.worldPosition + rayVec, own, GUARD_CHASE_DISTANCE, "OBSTACLE")
                    
                    if not ray[0]:
                        own["Alerted"] = True
                        exclamation.visible = True
            
            elif own["Timer"] > 0:
                own["Timer"] = -GUARD_ACTION_INTERVAL
                own["Moving"] = random() > 0.5
                own["Direction"] = "R" if random() > 0.5 else "L"
                
        elif ray[0] or player["Dead"]:
            own["Alerted"] = False
            exclamation.visible = False
            own["Direction"] = "R" if own["Direction"] == "L" else "L"


def processAnimation(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner
    armature = own.childrenRecursive["GuardArmature"] # type: BL_ArmatureObject
    hitPlayer = cont.sensors["HitPlayer"] # type: KX_TouchSensor
    
    animation = "Idle"
    
    if not own["Action"]:
        
        if own["Moving"]:
            animation = "Walk"
        
        # Invert armature direction
        if own["Direction"] == "L":
            armature.localScale.x = -1
        else:
            armature.localScale.x = 1
            
    elif own["Action"] == "Attack":
        actionFrame = int(armature.getActionFrame())
        anim = GUARD_ANIMS["Attack"]
        
        if actionFrame >= int(anim[0])+3 and actionFrame <= int(anim[0])+6:
            if hitPlayer.positive:
                
                if not hitPlayer.hitObject["Dead"]:
                    hitPlayer.hitObject["Dead"] = True
                    obj = own.scene.addObject("GuardPow")
                    obj.worldPosition = hitPlayer.owner.worldPosition
        
        if actionFrame >= int(anim[1])-2 and actionFrame <= int(anim[1]):
            own["Action"] = ""
        else:
            animation = "Attack"
        
    animation = GUARD_ANIMS[animation]
    armature.playAction("Guard", animation[0], animation[1], blendin=2)


def processMovement(cont):
    # type: (SCA_PythonController) -> None
    
    own = cont.owner
    
    moveVec = Vector([0.0, 0.0, 0.0])
    
    if own["Moving"] and not own["Action"]:
        moveVec.x = GUARD_MOV_SPEED
        
    if own["Direction"] == "L":
        moveVec.x *= -1
        
    own.applyMovement(moveVec)
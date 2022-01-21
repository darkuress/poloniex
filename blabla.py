import unreal
import usd_unreal.export_level, usd_unreal.utils
from pxr import Usd, UsdGeom, UsdUtils, Sdf

asset_path = ""
file_path = "D:/Perforce/VHE/USD"
content_directory  = "D:/Perforce/VHE/depot/vhe/Content"
relative_directory = "."
root_name = "/root"
unit_scale = 1
stage_up_axis = 'z'
#export_assets : set to False if you have already exported the different usd files for each assets. It will have to be in the right directory
export_assets = True
selection_only = False
USDExportLevel = usd_unreal.export_level.USDExportLevel()
folders_list = {}
                        

def set_file_path() :
    global file_path;
    global content_directory

    content_directory = unreal.SystemLibrary.get_project_content_directory()
    print ("content directory : "+content_directory)
    temp_path = content_directory.rstrip("/")
    file_path = temp_path.rstrip("Content") + "USD"
    print("file path : " + file_path)
    
	
    #create a Map that contains the name of the different meshes used (our assets) linked to an array of their instances in the scene
def create_map_of_meshes():
    global folders_list;

    if selection_only == False :
        listActors = unreal.EditorLevelLibrary.get_all_level_actors()
    else :
        listActors = unreal.EditorLevelLibrary.get_selected_level_actors()

    # this line works with only StaticMeshActor.
    #listMeshActors = unreal.EditorFilterLibrary.by_class(listActors, unreal.StaticMeshActor)
    myMap = {}
    
    for actor in listActors:
        if USDExportLevel.should_export_actor(actor):

            #let us get also the list of folders that we have in the outliner
            folder_path = actor.get_folder_path()
            if folder_path in folders_list == False:
                folders_list[folder_path] = True
            sm_array = actor.get_components_by_class(unreal.StaticMeshComponent.static_class())
            for smc in sm_array:
                sm = smc.static_mesh
                if sm is not None:
                    #print actor.get_name() #ACTUALLY, ID name in the scene, not the name that is visible in the outliner
                    #print actor.get_folder_path() #folder in the scene
                    #print actor.get_path_name() #path_name is the full path based on the level. exemple : /Game/Maps/myMap.PersistentLevel.Sphere2
                    full_name = sm.get_full_name()
                    if full_name in myMap :
                        #there's a previous actor that uses the same asset
                        myArray = myMap[full_name]
                        myArray.append(actor)

                    else :
                        #first actor to use that asset
                        newArray = unreal.Array(unreal.Actor)
                        newArray.append(actor)
                        myMap[full_name]=newArray

    return myMap

def get_first_usd_stage_actor():
    listActors = unreal.EditorLevelLibrary.get_all_level_actors()
    listUsdStageActors = unreal.EditorFilterLibrary.by_class(listActors, unreal.UsdStageActor)
    firstStageActor = listUsdStageActors[0]
    if (firstStageActor == None) :
	    return None
    return firstStageActor

def get_opened_stages():
    stagecache =  UsdUtils.StageCache.Get()
    return stagecache.GetAllStages()

def get_usd_node_from_path(usd_name):
    stages = get_opened_stages()
    stage = stages[0]
    usd_node = stage.GetPrimAtPath(usd_name)
    return usd_node

def get_actor_from_name(actorName):
    unreal.log_warning(actorName)
    listActors = unreal.EditorLevelLibrary.get_all_level_actors()
    myActor = unreal.EditorFilterLibrary.by_id_name(listActors, actorName)
    if len(myActor)>0:
        return myActor[0]
    else:
        return None


def create_usd_stage_actor():
    usdStage = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.UsdStageActor,[0,0,0])
    usdStage.set_actor_label("UsdScene")


def list_meshes():
    print("LATEST")
    myMap = create_map_of_meshes()

    print("THE FULL LIST")
    myItems = myMap.items()
    for Item in myItems :
	    currentName = Item[0]
	    print("------ " + currentName + " : ")
	    currentArray = Item[1]
	    for actor in currentArray :
		    print( actor.get_actor_label() + " ID : " + actor.get_name())	

def get_usd_asset_filename_from_actor(actor, directory):
    mesh_name = "none.none"
    if actor.static_mesh_component.static_mesh is not None:
        mesh_name = actor.static_mesh_component.static_mesh.get_full_name()
    return get_usd_asset_filename(mesh_name,directory)
 #   filename = directory + '/Assets/' + mesh_name.rsplit('.')[1] + '.usda'
 #   return filename

def get_usd_asset_filename(full_name,directory):
    filename = directory + '/Assets/' + full_name.rsplit('.')[1] + '.usda'
    return filename


# export 1 single static mesh. full_name of static mesh, smc is static mesh component. return the name of the usda file created
def export_mesh_to_usd(full_name,smc, directory):
    task = unreal.AssetExportTask()
    task.object = smc.static_mesh
    task.filename = get_usd_asset_filename(full_name, directory)
    task.selected = False
    task.replace_identical = True
    task.prompt = False
    task.automated = True
    unreal.Exporter.run_asset_export_task(task)

    #let's add the asset information
    unreal.log_warning("adding asset information for :" + full_name)
    stage = Usd.Stage.Open(task.filename)
    usd_prim = stage.GetDefaultPrim()
    model = Usd.ModelAPI(usd_prim)
    model.SetAssetIdentifier(task.filename)
    model.SetAssetName(full_name.rsplit('.')[1])
    stage.Save()

    return task.filename


def export_all_meshes_as_usd_assets(directory):
    all_meshes = create_map_of_meshes()
    for mesh in all_meshes.items():
        full_name = mesh[0] #value of the key.
        actor = mesh[1][0]
        sm_array = actor.get_components_by_class(unreal.StaticMeshComponent.static_class())
        for smc in sm_array:
            if smc.static_mesh is not None:
                sm_name = smc.static_mesh.get_full_name()
                if (sm_name == full_name) :
                    export_mesh_to_usd(full_name,smc,directory)
                    break

#####	#copied from attribute.py - removed some test that should probably be added back. Modified the convert functions

def convert_location_from_unreal(v, unit_scale):
    return (v[0] * unit_scale, -v[1] * unit_scale, v[2] * unit_scale)


def convert_rotation_from_unreal(v, unit_scale=1):
    return(v[0],-v[1],-v[2])
    #return (v[0], -v[2], v[1])


def convert_scale_from_unreal(v, unit_scale=1):
    return (v[0], v[1], v[2])



def usd_transform_from_unreal_transform(unreal_transform, unit_scale=1.0, up_axis='y'):
	location = convert_location_from_unreal(unreal_transform.translation.to_tuple(), unit_scale)
	rotation = convert_rotation_from_unreal(unreal_transform.rotation.rotator().to_tuple(), unit_scale)
	scale = convert_scale_from_unreal(unreal_transform.scale3d.to_tuple(), unit_scale)
	return (location, rotation, scale)

    #usd_prim is camera_prim, actor is a CineCameraActor
def handle_transform_camera(usd_prim, actor):
    global unit_scale
    global stage_up_axis

    if actor.root_component == None:
        return
    unreal_transform = actor.root_component.get_relative_transform()
    unreal_location = unreal_transform.translation
    unreal_rotation = unreal_transform.rotation.rotator()
    rotz = unreal.Rotator(90,0,0)
    additional_rotation = unreal.Rotator(0,90,0)

    if stage_up_axis == 'z':
        additional_rotation = additional_rotation.combine(rotz)

    unreal_rotation = additional_rotation.combine(unreal_rotation)
    
    location = convert_location_from_unreal(unreal_location.to_tuple(),unit_scale)
    rotation = convert_rotation_from_unreal(unreal_rotation.to_tuple(), unit_scale)
    scale = convert_scale_from_unreal(unreal_transform.scale3d.to_tuple(), unit_scale)

    usd_transform = (location, rotation, scale)
    

    #usd_transform = usd_transform_from_unreal_transform(unreal_transform, unit_scale, stage_up_axis)
	
    xform_api = UsdGeom.XformCommonAPI(usd_prim)

    xform_api.SetTranslate(usd_transform[0])
    xform_api.SetRotate(usd_transform[1], UsdGeom.XformCommonAPI.RotationOrderXYZ)
    xform_api.SetScale(usd_transform[2])

def handle_transform(usd_prim, actor):
	global unit_scale
	global stage_up_axis

	if actor.root_component == None:
		return
	unreal_transform = actor.root_component.get_relative_transform()

	usd_transform = usd_transform_from_unreal_transform(unreal_transform, unit_scale, stage_up_axis)
	
	xform_api = UsdGeom.XformCommonAPI(usd_prim)

	xform_api.SetTranslate(usd_transform[0])
	xform_api.SetRotate(usd_transform[1], UsdGeom.XformCommonAPI.RotationOrderXYZ)
	xform_api.SetScale(usd_transform[2])

def handle_transform_component(usd_prim, component):
	global unit_scale
	global stage_up_axis

	unreal_transform = component.get_relative_transform()

	usd_transform = usd_transform_from_unreal_transform(unreal_transform, unit_scale, stage_up_axis)
	
	xform_api = UsdGeom.XformCommonAPI(usd_prim)

	xform_api.SetTranslate(usd_transform[0])
	xform_api.SetRotate(usd_transform[1], UsdGeom.XformCommonAPI.RotationOrderXYZ)
	xform_api.SetScale(usd_transform[2])

#####			END OF MODIFIED export_level.py CODE

        
def add_component_material_list_to_usd_prim(usd_prim, smc):
    xform_prim = usd_prim
    material_list = smc.get_editor_property("override_materials")
    usd_material_list = []
        #for now, because the material are not exported when exporting the assets,
        #if we do not overide the materials on the actor, we will still do an override on the usd nod
    
    sm = smc.static_mesh
    slot = 0
        #we're only considering the LOD 0
    num_sections = sm.get_num_sections(0)
    
    if len(material_list) == 0 :
        while slot< num_sections:
            material = sm.get_material(slot)
            if (material != None):
                usd_material_list.append(material.get_path_name())
            slot = slot +1
        
    for material in material_list :
        if (material != None):
            usd_material_list.append(material.get_path_name())
        else:
            if slot < num_sections:
                unreal.log_warning("in here with slot = " + str(slot))
                mat2 = sm.get_material(slot)
                if (mat2 != None):
                    usd_material_list.append(mat2.get_path_name())
        slot = slot+1
        
    if usd_material_list != [] :
        unrealMaterials = xform_prim.CreateAttribute("unrealMaterials", Sdf.ValueTypeNames.StringArray)
        unrealMaterials.Set(usd_material_list)


def add_folders_to_stage(stage = None):
    global folders_list
    for folders in folders_list:
        print("folders = "+ str(folders))
        if folders != 'None' :
            folder_string = str(folders)
        
def add_static_mesh_component_to_stage(smc, stage):
    global file_path
    global root_name
    global relative_directory
    name = root_name + usd_unreal.utils.get_usd_path_from_actor_labels(smc.get_owner())+"/"+smc.get_name()
    nf = stage.DefinePrim(name, 'Xform')
    mesh_name = "none.none"
    if smc.static_mesh is not None:
        smc.static_mesh.get_full_name()
        usd_asset_name = get_usd_asset_filename(mesh_name,relative_directory)
        nf.GetReferences().AddReference(usd_asset_name)
        handle_transform_component(nf, smc)
        usd_child_name = name +"/" + smc.static_mesh.get_name()
        usd_prim = stage.OverridePrim(usd_child_name)
    add_component_material_list_to_usd_prim(usd_prim,smc)


def export_visibility(actor, usd_node, stage):
    global USDExportLevel
    USDExportLevel.stage = stage
    visibility = True
    print("inside the function for "+actor.get_name())

    if usd_node.IsA(UsdGeom.Imageable) == True:
        if hasattr(actor.root_component,"visible"):
            visibility = actor.root_component.visible
            #print("for actor "+actor.get_name()+" visibility is "+str(visibility))
        if visibility == True:
            if actor.hidden == True:
                visibility = False

        usd_visibility = usd_node.GetAttribute(UsdGeom.Tokens.visibility)
        if visibility == True:
            usd_visibility.Set(UsdGeom.Tokens.inherited)
        else :
            usd_visibility.Set(UsdGeom.Tokens.invisible)
    


    

	#actor should be a StacticMeshActor. stage is a UsdStage
def add_actor_to_stage(actor,stage):
    global file_path
    global root_name
    global relative_directory
    #print("root_name ="+root_name)
    folder = actor.get_folder_path()
    
    if folder.is_none() == False :
        folder_name = usd_unreal.utils.clean_node_name(str(folder))
        name = root_name + '/' + folder_name +  usd_unreal.utils.get_usd_path_from_actor_labels(actor)
    else :
        name = root_name + usd_unreal.utils.get_usd_path_from_actor_labels(actor)
   
    unreal.log_warning("adding actor " + name)
    nf = stage.DefinePrim(name, 'Xform')

    #reference the usd asset file
    usd_asset_name = get_usd_asset_filename_from_actor(actor,relative_directory)
    nf.GetReferences().AddReference(usd_asset_name)

    #add transform information
    handle_transform(nf, actor)

    
    #since we are referencing the static mesh actor, the actual mesh is one level below
    #to assign the materials, we need to override the referenced usd_prim
    if actor.static_mesh_component.static_mesh is not None:
        usd_child_name = name +"/" + actor.static_mesh_component.static_mesh.get_name()
        usd_prim = stage.OverridePrim(usd_child_name)
        add_component_material_list_to_usd_prim(usd_prim,actor.static_mesh_component)
        #check visibility
        export_visibility(actor, usd_prim, stage)



def add_camera_to_stage(actor, stage):
    global file_path
    global root_name
    global relative_directory
    #print("root_name ="+root_name)
    global USDExportLevel
    USDExportLevel.stage = stage
    
    if isinstance(actor, unreal.CineCameraActor):
        name = root_name + usd_unreal.utils.get_usd_path_from_actor_labels(actor)

        usd_camera = UsdGeom.Camera.Define(stage,name)
        usd_camera_prim = usd_camera.GetPrim()
        usd_camera_prim.SetMetadata('kind', 'component')    #to see if we want to use assembly instead
        
        for attribute in usd_unreal.attributes.camera.attributes:
            value = usd_unreal.attributes.camera.get_from_unreal_actor(attribute, actor)
            if value != None:
	            attribute.construct_usd_attribute(usd_camera).Set(value=value)

        handle_transform_camera(usd_camera_prim, actor)
        export_visibility(actor, usd_camera_prim, stage)
        

        #old wrong method of exporting the camera.
        # Rotation correction. Note: This needs to later be moved to be the last op in the xform order
        #rotate_y_op = usd_camera.AddRotateYOp(opSuffix='rotateAxis')
        #rotate_y_op.Set(-90)
        #USDExportLevel.export_visibility(actor, usd_camera)
        # the rotate_y_op is being moved to the last op during this steps:
        #USDExportLevel.export_transform_attributes(actor, usd_camera)
               
#export the entire level.
def export(name):
    global file_path
    global relative_directory
    global root_name
    global USDExportLevel
    global selection_only

    set_file_path()
    filename = file_path + '/'+name
    root_name = '/' + unreal.EditorLevelLibrary.get_editor_world().get_name()
    
    #first we export all the different assets that we will reference after
    if export_assets == True :
        export_all_meshes_as_usd_assets(file_path)

    #onto the usda layer that will reference those assets
    stagecache =  UsdUtils.StageCache.Get()
    stagecachecontext = Usd.StageCacheContext(stagecache)
    stage = Usd.Stage.CreateNew(filename)
    nf = stage.DefinePrim(root_name, 'Xform')
    stage.SetDefaultPrim(nf)
    UsdGeom.SetStageUpAxis(stage,'Z')

    #now we add the actors to the usd stage, referencing the usd asset files we exported above.

    if selection_only == False :
        listActors = unreal.EditorLevelLibrary.get_all_level_actors()
    else :
        listActors = unreal.EditorLevelLibrary.get_selected_level_actors()
    
    for actor in listActors :
        if isinstance(actor,unreal.StaticMeshActor):
            add_actor_to_stage(actor, stage)
        elif isinstance(actor, unreal.CineCameraActor):
            add_camera_to_stage(actor, stage)
        elif USDExportLevel.should_export_actor(actor):
            sm_array = actor.get_components_by_class(unreal.StaticMeshComponent.static_class())
            for smc in sm_array:
                add_static_mesh_component_to_stage(smc,stage)

    stage.GetRootLayer().Save()


def export_scene(name) :
    global selection_only
    selection_only = False
    export(name)

def export_selection(name):
    global selection_only
    selection_only = True
    export(name)


#when we have already a usdActor in our scene, and have made modification, and we want to save it with a different name:
def save_as(name):
    global file_path
    global relative_directory
    global root_name
    global USDExportLevel
    relative_directory = usd_unreal.utils.convert_to_relative_path(file_path)
    filename = file_path + '/'+name
    root_name = '/' + unreal.EditorLevelLibrary.get_editor_world().get_name()

    stages = get_opened_stages()
    stage = stages[0]
    print("saving stage at : " + filename)
    stage.Export(filename)
    
		




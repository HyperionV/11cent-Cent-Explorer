#include "scene_registry.hpp"

SceneRegistry::SceneRegistry() {
    scenes.resize(static_cast<int>(SceneID::SIZE));
    scenes[static_cast<int>(SceneID::MENU)] = new Menu();
}

SceneRegistry::~SceneRegistry() {
    for(Scene* scene : scenes)
        delete scene;
    scenes.clear();
    if(_instance) delete _instance;
}

SceneRegistry* SceneRegistry::instance() {
    if(!_instance) _instance = new SceneRegistry();
    return _instance;
}

Scene* SceneRegistry::scene(SceneID type) {
    unsigned int ID = static_cast<unsigned int>(type);
    if(ID >= scenes.size()) return nullptr;
    return scenes[ID];
}

SceneRegistry* SceneRegistry::_instance = nullptr;
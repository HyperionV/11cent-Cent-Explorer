#ifndef SCENE_REGISTRY_HPP_
#define SCENE_REGISTRY_HPP_

#include <vector>

#include "menu.hpp"

enum class SceneID {
    MENU,
    SIZE
};

class SceneRegistry {
private:
    static SceneRegistry* _instance;
    std::vector<Scene*> scenes;

    SceneRegistry();
    ~SceneRegistry();

public:
    static SceneRegistry* instance();
    Scene* scene(SceneID type);
};

#endif
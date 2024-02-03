#ifndef SCENE_HPP_
#define SCENE_HPP_

class Scene {
private:

public:
	virtual void update() = 0;
	virtual void draw() = 0;
};

#endif // SCENE_HPP_
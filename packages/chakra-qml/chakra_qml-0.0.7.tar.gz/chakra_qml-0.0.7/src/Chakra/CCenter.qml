pragma ComponentBehavior: Bound

import QtQuick

/*
    CCenter - 居中容器组件

    == 组件库特有属性 ==
    无特有属性，子元素自动居中显示
*/
Item {
    id: root

    // 内容
    default property alias content: container.data

    Item {
        id: container
        anchors.centerIn: parent
        width: childrenRect.width
        height: childrenRect.height
    }
}

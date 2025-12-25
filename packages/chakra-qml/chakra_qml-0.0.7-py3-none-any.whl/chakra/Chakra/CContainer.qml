pragma ComponentBehavior: Bound

import QtQuick

/*
    CContainer - 容器组件

    == 组件库特有属性 ==
    size          : 最大宽度尺寸，可选 "sm" | "md" | "lg" | "xl" | "full"，默认 "lg"
    centerContent : 是否居中内容，默认 true
    paddingX      : 水平内边距，默认 AppStyle.spacing4
*/
Item {
    id: root

    // 最大宽度
    property string size: "lg"  // sm, md, lg, xl, full
    property int maxWidth: size === "full" ? (parent ? parent.width : 9999) : AppStyle.getContainerMaxWidth(size)

    // 是否居中
    property bool centerContent: true

    // 内边距
    property int paddingX: AppStyle.spacing4

    // 内容
    default property alias content: contentArea.data

    width: parent ? parent.width : 0
    implicitHeight: contentArea.childrenRect.height

    Item {
        id: contentArea
        width: Math.min(root.maxWidth, parent.width - root.paddingX * 2)
        height: childrenRect.height
        anchors.horizontalCenter: root.centerContent ? parent.horizontalCenter : undefined
        x: root.centerContent ? 0 : root.paddingX
    }
}

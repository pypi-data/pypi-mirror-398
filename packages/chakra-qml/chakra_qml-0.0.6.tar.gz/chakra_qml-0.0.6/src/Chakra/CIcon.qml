import QtQuick

/*
    CIcon - 图标组件

    == 组件库特有属性 ==
    name      : 图标名称（如 "house", "user", "gear", "heart"），默认 ""
    size      : 图标大小（像素），默认 16
    iconColor : 图标颜色，默认 AppStyle.textColor
*/
Text {
    id: root

    // 图标名称 (例如: "house", "user", "gear", "heart")
    property string name: ""

    // 尺寸
    property int size: 16

    // 颜色
    property color iconColor: AppStyle.textColor

    // 使用 Icons 单例中的共享字体
    font.family: Icons.fontFamily
    font.pixelSize: root.size
    color: root.iconColor
    text: Icons.icons[root.name] || ""

    horizontalAlignment: Text.AlignHCenter
    verticalAlignment: Text.AlignVCenter
}

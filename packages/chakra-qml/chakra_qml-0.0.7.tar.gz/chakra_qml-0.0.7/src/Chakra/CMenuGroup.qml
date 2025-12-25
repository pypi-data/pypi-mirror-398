import QtQuick

/*
    CMenuGroup - 菜单分组组件

    == 组件库特有属性 ==
    title : 分组标题，默认 ""
*/
Column {
    id: root

    // 组标题
    property string title: ""

    // 子菜单项
    default property alias items: itemsColumn.children

    width: parent ? parent.width : 180
    spacing: 2

    // 组标题
    Text {
        visible: root.title !== ""
        text: root.title
        font.pixelSize: AppStyle.fontSizeXs
        font.weight: Font.Medium
        color: AppStyle.textMuted
        leftPadding: AppStyle.spacing3
        topPadding: AppStyle.spacing2
        bottomPadding: AppStyle.spacing1
    }

    // 菜单项容器
    Column {
        id: itemsColumn
        width: parent.width
        spacing: 2
    }
}

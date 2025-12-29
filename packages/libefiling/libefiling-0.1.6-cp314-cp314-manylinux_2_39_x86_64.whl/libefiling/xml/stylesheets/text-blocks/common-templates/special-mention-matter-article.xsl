<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:jp="http://www.jpo.go.jp">

    <!-- this xslt was created with reference to pat_common.xsl
         of Internet Application Software version i5.30 provided by JPO -->

    <!-- ====================================================================
         jp:special-mention-matter-article
         ====================================================================-->
    <!-- 特記事項 -->
    <xsl:template name="convert-special-mention-matter-article">
        <xsl:param name="article" as="xs:string" />
        <xsl:param name="kind-of-law" as="xs:string" />
        <xsl:value-of
            select="key('articles-table-key', $article || '-' || $kind-of-law, $articles-table)/@value" />
    </xsl:template>

    <xsl:key name="articles-table-key" match="item" use="@key" />
    <xsl:variable name="articles-table">
        <!-- 特許 -->
        <item key="010-patent" value="通常出願" />
        <item key="030-patent" value="昭和６２年改正前特許法第３８条ただし書の規定による特許出願" />
        <item key="040-patent" value="特許法第４４条第１項の規定による特許出願" />
        <item key="041-patent" value="平成５年改正前特許法第４４条第１項の規定による特許出願" />
        <item key="051-patent" value="特許法第４６条第１項の規定による特許出願" />
        <item key="052-patent" value="特許法第４６条第２項の規定による特許出願" />
        <item key="053-patent" value="昭和６０年改正前特許法第４５条第１項の規定による特許出願" />
        <item key="054-patent" value="平成５年改正前特許法第４６条第１項の規定による特許出願" />
        <item key="055-patent" value="平成５年改正前特許法第４６条第２項の規定による特許出願" />
        <item key="060-patent" value="昭和６０年改正前特許法第５３条第４項に規定する特許出願" />
        <item key="070-patent" value="特許法第４６条の２第１項の規定による実用新案登録に基づく特許出願" />
        <item key="511-patent" value="特許法第３０条第１項の規定の適用を受けようとする特許出願" />
        <item key="512-patent" value="特許法第３０条第３項の規定の適用を受けようとする特許出願" />
        <item key="513-patent" value="平成５年改正前特許法第３０条第１項の規定の適用を受けようとする特許出願" />
        <item key="514-patent" value="平成５年改正前特許法第３０条第３項の規定の適用を受けようとする特許出願" />
        <item key="515-patent" value="平成２３年改正前特許法第３０条第１項の規定の適用を受けようとする特許出願" />
        <item key="516-patent" value="平成２３年改正前特許法第３０条第３項の規定の適用を受けようとする特許出願" />
        <item key="517-patent" value="特許法第３０条第２項の規定の適用を受けようとする特許出願" />
        <item key="521-patent" value="特許法第３６条の２第１項の規定による特許出願" />
        <item key="526-patent" value="特許法第３８条の３の規定による特許出願" />
        <item key="531-patent" value="特許法第１８４条の１４の規定により特許法第３０条第１項の規定の適用を受けようとする特許出願" />
        <item key="532-patent" value="特許法第１８４条の１４の規定により特許法第３０条第３項の規定の適用を受けようとする特許出願" />
        <item key="533-patent" value="特許法第１８４条の１４の規定により平成２３年改正前特許法第３０条第１項の規定の適用を受けようとする特許出願" />
        <item key="534-patent" value="特許法第１８４条の１４の規定により平成２３年改正前特許法第３０条第３項の規定の適用を受けようとする特許出願" />
        <item key="535-patent" value="特許法第１８４条の１４の規定により特許法第３０条第２項の規定の適用を受けようとする特許出願" />
        <item key="999-patent" value="条文記載誤り" />

        <!-- 実用新案 -->
        <item key="010-utility" value="通常出願" />
        <item key="040-utility" value="実用新案法第９条第１項において準用する特許法第４４条第１項の規定による実用新案登録出願" />
        <item key="041-utility" value="平成５年改正前実用新案法第９条第１項において準用する平成５年改正前特許法第４４条第１項の規定による実用新案登録出願" />
        <item key="042-utility" value="実用新案法第１１条第１項において準用する特許法第４４条第１項の規定による実用新案登録出願" />
        <item key="051-utility" value="実用新案法第８条第１項の規定による実用新案登録出願" />
        <item key="052-utility" value="実用新案法第８条第２項の規定による実用新案登録出願" />
        <item key="054-utility" value="平成５年改正前実用新案法第８条第１項の規定による実用新案登録出願" />
        <item key="055-utility" value="平成５年改正前実用新案法第８条第２項の規定による実用新案登録出願" />
        <item key="056-utility" value="平成５年改正法附則第５条第１項の規定による実用新案登録出願" />
        <item key="057-utility" value="平成５年改正法附則第５条第５項の規定による実用新案登録出願" />
        <item key="058-utility" value="実用新案法第１０条第１項の規定による実用新案登録出願" />
        <item key="059-utility" value="実用新案法第１０条第２項の規定による実用新案登録出願" />
        <item key="060-utility" value="昭和６０年改正前実用新案法第１３条において準用する昭和６０年改正前特許法第５３条第４項に規定する実用新案登録出願" />
        <item key="511-utility" value="実用新案法第９条第１項において準用する特許法第３０条第１項の規定の適用を受けようとする実用新案登録出願" />
        <item key="512-utility" value="実用新案法第９条第１項において準用する特許法第３０条第３項の規定の適用を受けようとする実用新案登録出願" />
        <item key="513-utility"
            value="平成５年改正前実用新案法第９条第１項において準用する平成５年改正前特許法第３０条第１項の規定の適用を受けようとする実用新案登録出願" />
        <item key="514-utility"
            value="平成５年改正前実用新案法第９条第１項において準用する平成５年改正前特許法第３０条第３項の規定の適用を受けようとする実用新案登録出願" />
        <item key="515-utility" value="実用新案法第１１条第１項において準用する特許法第３０条第１項の規定の適用を受けようとする実用新案登録出願" />
        <item key="516-utility" value="実用新案法第１１条第１項において準用する特許法第３０条第３項の規定の適用を受けようとする実用新案登録出願" />
        <item key="517-utility" value="実用新案法第１１条第１項において準用する平成２３年改正前特許法第３０条第１項の規定の適用を受けようとする実用新案登録出願" />
        <item key="518-utility" value="実用新案法第１１条第１項において準用する平成２３年改正前特許法第３０条第３項の規定の適用を受けようとする実用新案登録出願" />
        <item key="519-utility" value="実用新案法第１１条第１項において準用する特許法第３０条第２項の規定の適用を受けようとする実用新案登録出願" />
        <item key="531-utility"
            value="実用新-utility案法第４８条の１５第３項で準用する特許法第１８４条の１４の規定により実用新案法第１１条第１項で準用する特許法第３０条第１項の規定の適用を受けようとする実用新案登録出願" />
        <item key="532-utility"
            value="実用新-utility案法第４８条の１５第３項で準用する特許法第１８４条の１４の規定により実用新案法第１１条第１項で準用する特許法第３０条第３項の規定の適用を受けようとする実用新案登録出願" />
        <item key="533-utility"
            value="実用新-utility案法第４８条の１５第３項で準用する特許法第１８４条の１４の規定により実用新案法第１１条第１項で準用する平成２３年改正前特許法第３０条第１項の規定の適用を受けようとする実用新案登録出願" />
        <item key="534-utility"
            value="実用新-utility案法第４８条の１５第３項で準用する特許法第１８４条の１４の規定により実用新案法第１１条第１項で準用する平成２３年改正前特許法第３０条第３項の規定の適用を受けようとする実用新案登録出願" />
        <item key="535-utility"
            value="実用新-utility案法第４８条の１５第３項で準用する特許法第１８４条の１４の規定により実用新案法第１１条第１項で準用する特許法第３０条第２項の規定の適用を受けようとする実用新案登録出願" />
        <item key="999-utility" value="条文記載誤り" />
    </xsl:variable>

</xsl:stylesheet>
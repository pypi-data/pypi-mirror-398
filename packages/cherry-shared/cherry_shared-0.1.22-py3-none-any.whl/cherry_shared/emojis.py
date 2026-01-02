custom_emoji = lambda emoji, id: f"<emoji id={id}>{emoji}</emoji>"

def state_emoji(state: bool):
    return "✅" if state else "❌"

class Emojis:
    """Emoji class for Bot, only edit this if you know what you're doing."""

    cherry = custom_emoji("✨", 5895729833744275779)

    like = custom_emoji("✨", 5893517852572392074)
    comment = custom_emoji("✨", 5893156134721693351)
    retweet = custom_emoji("✨", 5893471234997361693)
    bookmark = custom_emoji("✨", 5893042846369323539)

    money = custom_emoji("✨", 5895660860864470421)
    check = custom_emoji("👍", 5893133745057175853)
    dollar = custom_emoji("✨", 5893362129943141788)
    wallet = custom_emoji("✨", 5893323290553883709)

    chart = custom_emoji("👤", 5893471969436769954)
    up = custom_emoji("✨", 5893148871931993814)

    cup = custom_emoji("✨", 5893031576375139865)
    hourglass = custom_emoji("✨", 5895516919330512408)
    hashtag = custom_emoji("✨", 5893145968534100750)
    timer = custom_emoji("✨", 5893267082316881718)
    loading = custom_emoji("🟧", 5255814461515647475)

    spark = custom_emoji("✨", 5895440726610680712)
    rocket = custom_emoji("✨", 6179494264246901366)
    beating_heart = custom_emoji("✨", 5895729833744275779)
    fire = custom_emoji("✨", 5895276701809646261)
    trending = custom_emoji("✨", 5893214030880840476)
    link = custom_emoji("🔗", 5271604874419647061)

    twitter = custom_emoji("✨", 5895602629697871568)

    solana = custom_emoji("✨", 5895319771741690759)
    raydium = custom_emoji("💰", 5328025123893029024)
    pumpswap = custom_emoji("✨", 5895399202866863159)
    telegram = custom_emoji("✨", 5895584668144638872)

    positions = {
        1: "<emoji id=5893205921982585828>1️⃣</emoji>",
        2: "<emoji id=5893223965140197576>2️⃣</emoji>",
        3: "<emoji id=5893373975462944128>3️⃣</emoji>",
        4: "<emoji id=5895289127150034662>4️⃣</emoji>",
        5: "<emoji id=5893224721054440432>5️⃣</emoji>",
        6: "<emoji id=5893059734180732242>6️⃣</emoji>",
        7: "<emoji id=5893121873767570573>7️⃣</emoji>",
        8: "<emoji id=5893225468378750376>8️⃣</emoji>",
        9: "<emoji id=5895366990612142834>9️⃣</emoji>",
        10: "<emoji id=5893014783053011644>🔟</emoji>",
    }

    class progress_bar:
        start_empty = custom_emoji("✨", 5895723910984374701)
        mid_empty = custom_emoji("✨", 5895276319557557365)
        end_empty = custom_emoji("✨", 5893246878790721920)
        start_full = custom_emoji("🤞", 5893477965211113979)
        mid_full = custom_emoji("✨", 5893102138392844424)
        end_full = custom_emoji("✨", 5893073297687452787)

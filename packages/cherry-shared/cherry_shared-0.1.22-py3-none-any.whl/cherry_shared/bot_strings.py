from cherry_shared.constants import Constants
from cherry_shared.emojis import Emojis


class BotStrings:
    """Input strings class for Bot."""

    contact_us = f"{Emojis.solana} <a href='{Constants.website_link}'>Web / Dashboard</a> | {Emojis.telegram} <a href='{Constants.bot_link}'>Cherry BOT</a> | {Emojis.twitter} <a href='{Constants.twitter_link}'>Twitter / X</a>"

    admin_only_command = "**⚠️ Only chat admins can use this command.**"
    bounty_amount_too_low = (
        "The bounty amount is too low, please set it to at least {min_amount} {symbol}."
    )
    cancel = "Cancel"
    cant_do_this = (
        "I can't do this. 😐 Please check if I have all the required permissions."
    )
    cant_do_this_to_admin = "I can't perform this action on admins."
    cant_do_this_to_me = "I can't do this to myself!"
    could_not_check_balance = "Couldn't verify your balance. Please try again."
    filter_already_exists = "This filter already exists. 😑"
    filter_not_found = "Mentioned Filter not found in this chat! 😐"
    invalid_user = "Invalid user id or username."
    make_me_admin = "**I need admin privileges to do this!**"
    max_gas_fee_exceeded = "ERR100: The Buy&Burn transaction didn't go through since the maximum gas you set in /settings is {max_gas} GWEI, the current gas is {current_gas} GWEI. "
    need_admin_privileges = "**⚠️ I need admin privileges to execute this operation.**"
    no_filter_found = "No filters found in this chat 😐"
    not_admin = "You can't do this as you're not an admin."
    operation_canceled = "Operation Canceled"
    raid_canceled = "Raid canceled"
    some_error_occurred = "Something went wrong. Please try again later. If the problem persists, contact Admin."
    some_error_occurred_no_balance = "ℹ️ An error happened during the buy&burn event, because of insufficient balance, please contact @EthDevMax to check and fix it."
    some_error_occurred_buyAndBurn = "ℹ️ An error happened during the buy&burn event, no ETH was used, please contact @EthDevMax to check and fix it."
    some_error_occurred_unknown = "ℹ️ An error happened during the buy&burn event, please contact @EthDevMax to check and fix it."
    contact_support = f"<i>Contact <a href={Constants.support_group_link}>Support</a> if you have any issues</i>"
    # Commands Help
    add_filter_command = (
        "**Add a filter to the chat.**\n\n"
        + "If you want to attach media to the filter you can use this command by mentioning the word and replying to a already sent message you want to set as response.\n\n"
        + "**Usage:** Reply to message with `/filter <trigger>`\n\n"
        + "**Example:**\n/filter /social\n\n"
        + "**OR**\n\n"
        + "You can also use this command by mentioning the word and sending the response message.\n\n"
        + "**Usage:** `/filter <trigger> <response>`\n\n"
        + "**Example:**\n/filter /social This is a social message.\n\n"
        + "__**Note:**__ The word will be case insensitive."
    )

    remove_filter_command = (
        "**Remove a filter from the chat.**\n\n"
        + "You can use this command by mentioning the word.\n\n"
        + "**Usage:** `/rmfilter <word>`\n\n"
        + "**Example:**\n/rmfilter /social"
    )

    ban_command = (
        "**Ban a user from the chat.**\n\n"
        + "Reply to a message sent by the user with this command to ban the user from the chat.\n\n"
        + "You can also use this command by mentioning the user."
    )

    unban_command = (
        "**Unban a already banned user from the chat.**\n\n"
        + "Reply to a message sent by the user with this command to unban the user from the chat.\n\n"
        + "You can also use this command by mentioning the user."
    )

    mute_command = (
        "**Mute a user in the chat.**\n\n"
        + "Reply to a message sent by the user with this command to mute the user in the chat.\n\n"
        + "You can also use this command by mentioning the user."
    )

    unmute_command = (
        "**Unmute a muted user in the chat.**\n\n"
        + "Reply to a message sent by the user with this command to unmute the user in the chat.\n\n"
        + "You can also use this command by mentioning the user."
    )

    quick_setup_guide_message = f"""{Emojis.fire} <b>Quick Setup Guide:</b>
/add - Connect token
/buybot - Configuration
/settings - Add socials to bot! 
/raid - Start X raids 
/Commands - List of all commands

{Emojis.dollar} Paid Features:
{Emojis.cup} BuyBot Trending: /Trend
{Emojis.hourglass} RaidBot Trending: /boost
{Emojis.chart} VolumeBot: /volume
{Emojis.money} HoldersBot: /holder
{Emojis.bookmark} Button ads: /advertise"""

    bot_start_message = f"""{Emojis.cup} <b>Cherry Telegram Bot</b>
    
{Emojis.check} Track buys in real-time, coordinate community raids, and boost your token's visibility with our premium features.

{quick_setup_guide_message}

{Emojis.solana} <a href='{Constants.website_link}'>Website / Dashboard</a> 
{Emojis.twitter} <a href='{Constants.twitter_link}'>Twitter / X</a> 
{Emojis.trending} <a href='{Constants.trending_channel_link}'>Trending hub</a>
    """
    # Long strings
    bot_welcome_message = f"""{Emojis.spark} <b>Cherry Bot added Successfully!</b>

{quick_setup_guide_message}

☝️ Make me admin to use commands!"""

    group_welcome_message = """Welcome {mention} to the group!"""

    private_start_message = f"""<b>The Ultimate Telegram Bot for Web3 Projects</b>
    
Enhance your group management and engage your community with Cherry Bot's powerful tools.

/add - Integrate a new project with Cherry Bot.
/trend - Boost your project's visibility in trending.
/raid - Start a raid to increase engagement and activity.
/boost - Purchase Raid Points for <a href='{Constants.raid_leaderboard}'>Raid Leaderboard</a>.
/portal - Create a portal
"""
    tutorial_message = """**Cherry Bot Tutorials**

**Quick Setup Guide: How to Order Cherry Trending**

👉 Access Cherry Bot on Telegram. [Link here](https://t.me/cherrytgbot).
👉 In the Cherry Bot DMs, write "/trend" and click on "Start".
👉 Send the token's Contract Address, Pair Address.
👉 Select the correct token type and confirm it.
👉 Send the token's group or portal link for tracking.
👉 Select your preferred trending slot.
👉 Send the payment to the shown address and click on "Verify Payment"

**Buy Bot** — gives you an overview of how to setup a launched token & presale token buy bot, using custom emoji/media/buy size/circulating supply.

https://www.youtube.com/watch?v=M7NNqKZhSJ8&t=4s

**Portal** —  gives you an overview of how to setup a working portal for your Telegram group using custom text & media.

https://www.youtube.com/watch?v=YFDWGgABTvI

**Welcome** — gives you an overview of how to setup an appealing  welcome message with customized text/media/buttons to greet your new Telegram members.

https://www.youtube.com/watch?v=dcmKhLK-qF8&t=15s

**Raid** — gives you an overview of normal/quick/bounty raid functions to increase your community engagement effort within your Telegram group.

https://www.youtube.com/watch?v=zHSQIIeyGA4&t=8s"""
    filling_format = """You can use the following fillings to customize the message. For example, you could mention a user in the welcome message.

Supported fillings:
- {first}: The user's first name.
- {last}: The user's last name.
- {fullname}: The user's full name.
- {username}: The user's username. If they don't have one, mentions the user instead.
- {mention}: Mentions the user with their firstname.
- {id}: The user's ID.
- {chatname}: The chat's name.
- {botname}: The bot's name.
- {botusername}: The bot's username.

Welcome {mention} to {chatname}!"""

    private_help_message = """**- What does Cherry bot do?** 
-- allows you to send us money for nothing /trend
— allows for the creation of raids /raid
--buybot to track/display buys of your token in your group. specify your token blockchain and contract in /settings. 
--portal to reduce spam and bots. use /setup
--It can function as an alternative for rose (/config,/mute,/ban,/filter,etc...)

**- How to start a raid? And how to cancel an on-going on?**
— Just send /raid to start a raid, it will ask you for the necessary data. If you want to cancel an on-going raid, send /stop. 

**- Is there any costs to use the bot?**
— All the bot features are totally free.
- premium services(trending, raid boosts) cost money."""

    group_user_help_message = """Here are the available group commands:

/filters: Show all chat filters - Displays all chat filters set in the group.
/admins: Show all chat admins - Lists all admins of the group.
/report: Report a user to admins - Reports a user to the group admins.
"""
    group_admin_help_message = """Here are the available commands:

/raid: Setup new Raid - Initiates a Raid event.
/stop: Stop Raid - Stops the ongoing Raid.
/restore: Allow users to send messages - Restores the ability for users to send messages.
/portal: Setup verification portal for the group - Sets up a verification portal for the group.
/settings: Configure group settings - Adjusts various group settings.
/config: Manage bot settings in the group - Manages bot settings within the group.
/ban: Ban a user from the group - Bans a user from the group.
/unban: Unban a user from the group - Removes a user ban from the group.
/mute: Mute a user in the group - Mutes a user in the group.
/unmute: Unmute a user in the group - Unmutes a previously muted user in the group.
/filter: Add or modify a chat filter - Adds or modifies a chat filter for the group.
/rmfilter: Remove a chat filter - Removes a chat filter from the group.
/add: Set the token address for the group - Sets the token address for the group.
/buybot: Buy Bot Settings - Purchases bot settings for the group.
/delete: Delete the group token - Deletes the group token.
/block: set or get blocked words in the chat.
/unblock: remove a blocked word in the chat.
"""
    private_owner_help_message = """Here are the available owner commands:

/commands: List of all Admin Commands - Displays a list of all admin commands.
/admin: List of all Admins - Lists all admins of the bot.
/broadcast: Send a message to all users - Sends a message to all users of the bot.
/message_to: Send a message to a specific user - Sends a message to a specific user.
/stats: View bot live stats - Displays live statistics of the bot.
/groups: View bot groups list - Shows a list of groups the bot is in.
"""
    custom_button_message = f"""**Buttons**
    
One of Telegram's most useful features is the ability to add buttons to your welcome messages. Buttons can be used to link to useful resources.

**How to add buttons?**
- The following syntax will create a button with the text "Telegram" which will open [telegram.org](https://telegram.org) when clicked.
-> `Telegram:https://telegram.org`

- You can add multiple buttons by making a new line for each button.

**Example**
```
Telegram:https://telegram.org
Website:https://telegram.org
```
"""

    ban_mute_success = "{from_mention} has {operation} {to_mention} successfully."
    unban_mute_success = "{from_mention} {operation} {to_mention}."

    portal_setup_message = "To setup the portal forward this message into a channel which I have admin in\n\nportal-{portal_id}"

    portal_verification_message = (
        """{group_name} is being protected by @{bot_username}."""
    )

    portal_verification_success = """Verified, you can join the **{group_name}** group using this temporary link:

{invite_link}

This link will expire in 5 minutes."""

    insufficient_balance_html = """<b>Insufficient Balance</b>
You do not have enough funds to perform this operation.

<b>Current Balance</b>: {balance} {token}

Please add more funds to the following wallet and try again:

🆔 Address: <code>{wallet_address}</code>"""

    insufficient_balance = """Insufficient Balance
You do not have enough funds to perform this operation.

Current Balance: {balance} {token}

Please add more funds to the following wallet and try again:

🆔 Address: {wallet_address}"""

    raid_command_message = f"""{Emojis.spark} <b>{{setup_by}} Started a New Raid</b> {Emojis.spark}
    
<b>Now configure the raid by clicking the buttons below.</b>
"""

    lock_message = (
        """🔒 <b>The group is now locked until this post reaches all the targets</b> """
    )
    raid_start_message = "<b>Raid in Progress</b>"

    raid_message = f"""{Emojis.rocket} {{header}} | {{points}} pts

{{progress_bar}}

{Emojis.like} Likes:  {{likes_stats}}
{Emojis.comment} Comments:  {{comments_stats}}
{{non_youtube_metrics}}
↳ <b>{{post_link}}</b>

{{leaderboard_msg}}"""
    non_youtube_raid_metrics = f"""{Emojis.retweet} {{share_type}}s:  {{shares_stats}}
{Emojis.bookmark} Bookmarks:  {{bookmarks_stats}}
"""

    raid_timeout = f"""{Emojis.timer} <b>Time is Up, Try Again!</b> | {{points}} pts

{Emojis.like} Likes: <b>{{final_likes}}</b>
{Emojis.comment} Comments: <b>{{final_comments}}</b>
{Emojis.retweet} {{share_type}}s: <b>{{final_shares}}</b>
{Emojis.bookmark} Bookmarks: <b>{{final_bookmarks}}</b>

↳ {{post_link}}

{{leaderboard_msg}}"""

    raid_success_msg = (
        f"{Emojis.spark} Raid Completed | <b>{{earned}}</b> Earned\n\n"
        f"{Emojis.timer} Duration : {{time_elapsed}}\n"
        f"↳ {{post_link}}\n\n"
        f"{Emojis.like} Likes: <b>{{likes}} {Emojis.check}</b>\n"
        f"{Emojis.comment} Comments: <b>{{comments}} {Emojis.check}</b>\n"
        f"{Emojis.retweet} {{share_type}}s: <b>{{shares}} {Emojis.check}</b>\n"
        f"{Emojis.bookmark} Bookmarks: <b>{{bookmarks}} {Emojis.check}</b>\n\n"
        f"{{leaderboard_msg}}\n\n"
        f"{{gp_link_hint}}"
    )
    boost_hint = f"<emoji id=5467519850576354798>❕</emoji> Next time use /Boost to start a {Emojis.rocket} <b>Boosted Raid</b> {Emojis.rocket} To reach maximum interaction: <a {Constants.cherry_docs}/setup-guides/setup-a-twitter-raid'>Learn more</a>"
    not_token_burnt_message = "ℹ No tokens were burnt as the bounty amount was not set."
    burn_tx_will_be_sent = f"{Emojis.fire} Buy and burn transactions will be sent in a few minutes. {Emojis.fire}"
    boosted_raid_success = (
        f"{Emojis.cup} You can claim your prize in the @cherrygame_io_bot. {Emojis.cup}"
    )
    raid_error_info_message = """⚠️ Raid Error Information ℹ️
    
{error_message}
    
Tx Hash: {tx_hash}
User: {user_id}
User Wallet: {user_wallet}
Group: {group_id}
Contract: {contract_address}
Chain: {chain}
"""
    token_event = f"""{Emojis.spark} <b>New @CherryTGBot Install</b>

<b><a href='{{group_link}}'>{{group_name}}</a> Just Installed @CherryTGBot - time to blast off</b><emoji id=5445284980978621387>🚀</emoji>

{{chart}}{Emojis.up} <a href='{{trending_channel}}'>Trending</a>"""

    trend_command_message = f"""{Emojis.check} Trending on <a href='{Constants.trending_channel_link}'>Cherry Trending</a> 
{Emojis.check} Entered into trending alerts
{Emojis.check} All time high alerts
{Emojis.check} Buy alerts
{Emojis.bookmark} MASS DM TO 300k+ Real Users
{Emojis.bookmark} Button Advertisement
"""

    raid_channel_message = f"""{Emojis.cup} <b><a href="{{chat_link}}">{{group_title}}</a></b> Started New Raid!\n
{Emojis.like} Likes: <b>{{target_likes}}</b>
{Emojis.comment} Comments: <b>{{target_comments}}</b>
{{non_youtube_info}}
{Emojis.twitter} <b>{{post_link}}</b>\n
{Emojis.cup} <a href='{Constants.raid_leaderboard}'>Raid Leaderboard #{{rank}}</a> | {{score}}\n
{contact_us}"""

    raid_channel_non_youtube = f"""{Emojis.retweet} {{share_type}}s: <b>{{target_shares}}</b>
{Emojis.bookmark} Bookmarks: <b>{{target_bookmarks}}</b>"""
    trend_message = (
        f"{Emojis.spark} <b>{{symbol}} Trending Boost</b> {Emojis.spark}\n\n"
        f"<b>Top {{position}} Trending</b> | <b>{{hours}} Hours {{promo}}</b>\n"
        f"Token: <b><a href='{{chart_link}}'>{{name}}</a></b> \n"
        f"Telegram: <b>{{portal_link}}</b>\n\n"
        f"{Emojis.money} Activate the boost by sending {{old_price}}<b>{{price}} {{chain_symbol}}</b> to: "
        f"<b><code>{{address}}</code></b>\n\n"
        f"Step 1: Send <b>{{price}} {{chain_symbol}}</b>\n"
        f"Step 2: Click <b>Verify Payment</b> to verify the transaction \n"
        f"Step 3: Watch <b>{{symbol}}</b> soar to the <b>Top {{position}}</b> trending shortly! \n\n"
        f"{contact_support}"
    )

    trend_select_period_message = f"""<a href='{{portal_link}}'>${{token_name}}</a> Trending Boost

<b>Top 3 Benefits</b> {Emojis.fire}

{Emojis.check} Trending on <a href='{Constants.trending_channel_link}'>Cherry Trending</a> website 
{Emojis.check} Entered into trending alerts
{Emojis.check} All time high alerts
{Emojis.check} Buy alerts
{Emojis.bookmark} MASS DM TO 300k+ Real Users
{Emojis.bookmark} Button Advertisement

<b>TOP 10 Benefits</b>

{Emojis.check} Trending on <a href='{Constants.trending_channel_link}'>Cherry Trending</a> website 
{Emojis.check} Entered into trending alerts
{Emojis.check} All time high alerts
{Emojis.check} Buy alerts
{Emojis.bookmark} Button Advertisement

 <b>Select the Period:</b>"""
    raid_bounty_channel_msg = f"""{Emojis.cherry} New @CherryTGBot Bounty Raid in <a href="{{group_link}}">{{group_name}}</a> {Emojis.cherry}

{Emojis.money} {{bounty_amount}} Buyback Bounty! {Emojis.money}

Raid for a buyback now: {{post_link}}

{Emojis.like} Likes: <b>{{current_likes}} (+{{target_likes}})</b>
{Emojis.comment} Comments: <b>{{current_comments}} (+{{target_comments}})</b>
{Emojis.retweet} {{share_type}}s: <b>{{current_shares}} (+{{target_shares}})</b>
{Emojis.bookmark} Bookmarks: <b>{{current_bookmarks}} (+{{target_bookmarks}})</b>

{{chart}}{Emojis.up} <a href="{{trending_channel}}">Trending</a>
"""

    promo_command = """
⚡️ <b>Set Up Your Wallets to Receive Referral Commissions!</b> ⚡️

Before you start earning, make sure your wallet addresses are configured so you receive referral commissions directly to your account.

🔗 <b>Required Wallets: {wallets}</b>

"""
    volume_command = f"""<b>Grow Your Token Volume With Ease!</b>

Works only for {Emojis.solana} Solana projects!
Dexes: <b>Raydium & <b>Pumpswap</b>

<b>How It Works:</b>
{Emojis.positions[1]} Choose your desired package
{Emojis.positions[2]} Complete your payment
{Emojis.positions[3]} Watch your Volume increase!

<b>Why Boost Your Volume?</b>
{Emojis.check} Show real-time traction
{Emojis.check} Rank higher on tracking sites
{Emojis.check} Attract investor attention
{Emojis.check} Get noticed by screening tools
{Emojis.check} Cost based on volume chosen.

{Emojis.timer} <i>Volume will begin within 1–5 minutes of purchase. If not, please contact <a href={Constants.support_group_link}>Support</a>.</i>"""

    volume_pay = (
        f"{Emojis.spark} <b><a href='{{token_link}}'>{{token_name}}</a> Volume Boost</b> {Emojis.spark}\n\n"
        f"{Emojis.money} Increase + ${{volume}} Volume to <b>{{token_name}}</b> by sending <b>{{price}} {{chain_symbol}}</b> to: "
        f"<b><code>{{address}}</code></b>\n\n"
        f"Step 1: Send <b>{{price}} {{chain_symbol}}</b>\n"
        f"Step 2: Click <b>Verify Payment</b> to verify the transaction \n"
        f"{Emojis.rocket} <b>Get ready for a Boost in the Tokens Volume!</b> {Emojis.rocket} \n\n"
        f"{{multi_wallet}}"
        f"{contact_support}"
    )

    entered_leaderboard = (
        f"{Emojis.cup} <b><a href='{{group_link}}'>{{group_name}}</a> Just Entered <a href='{Constants.raid_leaderboard}'>Raid Leaderboard</a></b>\n\n"
        f"{Emojis.up} Position: <b>#{{position}}</b>\n"
        f"{Emojis.bookmark} Raid Points: <b>{{points}}</b> {Emojis.spark}\n"
        f"{Emojis.chart} Points to Next Position: <b>{{points_to_next}}</b>\n\n"
        f"{{leaderboard_message}}\n\n"
        f"{contact_us}"
    )

    holder_command = f"""<b>Works only for {Emojis.solana} Solana projects!</b>

How It Works:
{Emojis.positions[1]} Choose your desired package
{Emojis.positions[2]} Complete your payment
{Emojis.positions[3]} Watch your holders increase — up to 20 per minute!

Why Boost Your Holders?
{Emojis.check} Show real-time growth
{Emojis.check} Attract investor attention
{Emojis.check} Get noticed by screening tools
{Emojis.check} No hidden fees — pay only for the service!

{Emojis.timer} Holders will stay for 1–2 weeks, depending on your package."""

    holder_pay = (
        f"{Emojis.spark} <b><a href='{{token_link}}'>{{token_name}}</a> Holder Boost</b> {Emojis.spark}\n\n"
        f"{Emojis.money} Add {{count}} Holders to <b>{{token_name}}</b> by sending <b>{{price}} {{chain_symbol}}</b> to: "
        f"<b><code>{{address}}</code></b>\n\n"
        f"Step 1: Send <b>{{price}} {{chain_symbol}}</b>\n"
        f"Step 2: Click <b>Verify Payment</b> to verify the transaction \n"
        f"{Emojis.rocket} <b>Get ready for a Boost in the Token Holders!</b> {Emojis.rocket} \n\n"
        f"{contact_support}"
    )

    commands_msg = f"""{Emojis.like} <b>User Commands</b>
/filters - View chat filters
/report - Report a user
/invite - Get invitation link
/leaderboard - View invite leaderboard

{Emojis.bookmark} <b>Admin Commands</b>
/sync - Sync admins
/portal - Setup verification portal
/block - Block specific words
/unblock - Unblock words
/settings - Group settings
/config - Bot settings
/ban - Ban user
/unban - Unban user
/mute - Mute user
/unmute - Unmute user
/filter - Add/modify filter
/rmfilter - Remove filter
/restore - Enable messaging

{Emojis.dollar} <b>Buy-bot Commands<b>
/add - Set token address
/delete - Remove group token
/buybot - Bot settings
/trend - Buy trending

{Emojis.cup} <b>Raid-bot Commands</b>
/raid - Start Raid
/stop - Stop Raid
/raidscore - View Raid Score
/boost - Buy Raid Points"""

    first_raid_message = (
        f"<b><a href='{{group_link}}'>{{group_name}}</a> Just Started a Raid with @CherryTGBot - Hit that like</b><emoji id=5445284980978621387>🚀</emoji>\n\n"
        f"{Emojis.spark} <a href='{{boost_link}}'>Boost Points</a> "
        f"{Emojis.cup} <a href='{Constants.raid_leaderboard}'>Leaderboard</a> "
        f"{Emojis.trending} <a href='{Constants.trending_channel_link}'>Trending</a>"
    )

    boost_command = (
        f"{Emojis.up} <b><a href='{Constants.raid_leaderboard}'>Raid Leaderboard</a> Boost</b>\n\n"
        f"{Emojis.bookmark} Top 3 appear on all raiding groups\n"
        f"{Emojis.check} Higher rank on <a href='{Constants.raid_leaderboard}'>Raid Leaderboard</a>\n"
        f"{Emojis.check} Entered into raid leaderboard alert\n"
        f"{Emojis.check} Raid start alerts"
    )

    boost_pay = (
        f"{Emojis.spark} <b>{{group_name}} Raid Points Boost</b> {Emojis.spark}\n\n"
        f"{Emojis.money} Add <b>+{{points}} Points</b> to <b>{{group_name}}</b> in leaderboard by sending <b>{{price}} {{chain_symbol}}</b> to: "
        f"<b><code>{{address}}</code></b>\n\n"
        f"Step 1: Send <b>{{price}} {{chain_symbol}}</b>\n"
        f"Step 2: Click <b>Verify Payment</b> to verify the transaction\n\n"
        f"{Emojis.rocket} <b>Get ready for a Boost in the leaderboard!</b> {Emojis.rocket} \n\n"
        f"{contact_support}"
    )

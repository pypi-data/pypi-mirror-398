# CDK Aspect Git Tagger

This is a CDK Aspect that will tag your CDK Stacks with the current git repo location for easier identification of
deployed stacks. Will create a `.git-url-tagger.json` file in the root of your project to store the git url.  This file
will be used to determine the git url for the stack.

### How to install

```shell
npm install @jjrawlins/cdk-git-tagger
```

or

```shell
yarn add @jjrawlins/cdk-git-tagger
```

### How to use

```python
import { GitUrlTagger } from '@jjrawlins/cdk-git-tagger';
import { App, Aspects, Stack, StackProps } from 'aws-cdk-lib';
import { Topic } from 'aws-cdk-lib/aws-sns';
import { Construct } from 'constructs';

export class MyStack extends Stack {
    constructor(scope: Construct, id: string, props: StackProps = {}) {
        super(scope, id, props);
        // define resources here...
        new Topic(this, 'MyTopic');
    }
}

const app = new App();

new MyStack(app, 'cdk-aspect-git-tagger-tester');
Aspects.of(app).add(new GitUrlTagger());
app.synth();
```

### Example Output

```json
{
  "Resources": {
    "MyTopic86869434": {
      "Type": "AWS::SNS::Topic",
      "Properties": {
        "Tags": [
          {
            "Key": "GitUrl",
            "Value": "https://github.com/jjrawlins/cdk-cool-construct.git"
          }
        ]
      }
    }
  }
}
```
